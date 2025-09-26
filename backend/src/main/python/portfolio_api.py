"""
FastAPI service for quantum portfolio optimization.
Replaces temporary JSON file communication with REST API endpoints.
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
import logging
import asyncio
import traceback
from datetime import datetime
import uuid

# Import optimization modules
import sys
import os

# Configure enhanced logging FIRST (before any imports that use logger)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - [%(funcName)s:%(lineno)d] - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('portfolio_api.log', mode='a')
    ]
)
logger = logging.getLogger(__name__)

# Log startup information
startup_time = datetime.now()
logger.info("=" * 60)
logger.info("QUANTUM PORTFOLIO OPTIMIZATION API STARTING UP")
logger.info("=" * 60)
logger.info(f"Startup time: {startup_time.isoformat()}")
logger.info(f"Python version: {sys.version}")
logger.info(f"Working directory: {os.getcwd()}")
logger.info(f"Script location: {__file__}")

# Test core module imports
try:
    import pandas as pd
    logger.info(f"Pandas version: {pd.__version__}")
except ImportError as e:
    logger.error(f"Pandas import failed: {e}")

try:
    import numpy as np
    logger.info(f"NumPy version: {np.__version__}")
except ImportError as e:
    logger.error(f"NumPy import failed: {e}")

try:
    import pypfopt
    logger.info(f"PyPortfolioOpt version: {pypfopt.__version__}")
except (ImportError, AttributeError) as e:
    logger.warning(f"PyPortfolioOpt version check failed: {e}")

try:
    import qiskit
    logger.info(f"Qiskit version: {qiskit.__version__}")
except (ImportError, AttributeError) as e:
    logger.warning(f"Qiskit version check failed: {e}")

# Add current directory to Python path for module imports
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)
    logger.info(f"Added to Python path: {current_dir}")

try:
    from classic_portfolio_opt import optimize_portfolio as classic_optimize
    logger.info("Successfully imported classic_portfolio_opt.optimize_portfolio")
except ImportError as e:
    logger.error(f"Failed to import classic_portfolio_opt: {e}")
    logger.error(f"Available files in {current_dir}: {os.listdir(current_dir)}")
    raise

try:
    from hybrid_portfolio_opt import classical_optimize, quantum_optimize
    logger.info("Successfully imported hybrid_portfolio_opt functions")
except ImportError as e:
    logger.error(f"Failed to import hybrid_portfolio_opt: {e}")
    logger.error(f"Available files in {current_dir}: {os.listdir(current_dir)}")
    raise

logger = logging.getLogger(__name__)

# Helper function to handle infinite values for JSON serialization
def sanitize_infinite_values(data):
    """Replace infinite values with large finite numbers for JSON compatibility."""
    import math
    
    if isinstance(data, dict):
        return {k: sanitize_infinite_values(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [sanitize_infinite_values(item) for item in data]
    elif isinstance(data, (int, float)):
        if math.isinf(data):
            if data > 0:
                return 1e10  # Large positive finite number
            else:
                return -1e10  # Large negative finite number
        elif math.isnan(data):
            return 0.0  # Replace NaN with 0
        else:
            return data
    else:
        return data

# FastAPI app instance
app = FastAPI(
    title="Quantum Portfolio Optimization API",
    description="REST API service for classical and quantum portfolio optimization",
    version="1.0.0"
)

# Track server startup time
startup_time = datetime.now()

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:8080"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request/Response Models
class StockDataPoint(BaseModel):
    symbol: str = Field(..., description="Stock symbol (e.g., AAPL)")
    date: str = Field(..., description="Date in YYYY-MM-DD format")
    close: float = Field(..., ge=0, description="Closing price")

class OptimizeRequest(BaseModel):
    stock_data: List[StockDataPoint] = Field(..., description="Historical stock price data")
    var_percent: float = Field(default=0.05, ge=0, le=1, description="Value at Risk percentage")
    qc_simulator: bool = Field(default=True, description="Use quantum simulator (true) or real backend (false)")

class ClassicalResult(BaseModel):
    weights: Dict[str, float] = Field(..., description="Portfolio weights by symbol")
    expected_annual_return: float = Field(..., description="Expected annual return")
    annual_volatility: float = Field(..., description="Annual volatility")
    sharpe_ratio: float = Field(..., description="Sharpe ratio")
    value_at_risk: float = Field(..., description="Value at Risk")

class QuantumResult(BaseModel):
    solution: Optional[List[int]] = Field(None, description="Quantum solution bitstring")
    objective_value: Optional[float] = Field(None, description="Objective function value")
    estimator_jobs_executed: Optional[int] = Field(None, description="Number of estimator jobs")
    sampler_jobs_executed: Optional[int] = Field(None, description="Number of sampler jobs")
    simulator_sampler_jobs_executed: Optional[int] = Field(None, description="Simulator sampler jobs")

class HybridResult(BaseModel):
    classical_weights: Dict[str, float] = Field(..., description="Classical optimization weights")
    classical_performance: Dict[str, float] = Field(..., description="Classical performance metrics")
    quantum_qaoa_result: QuantumResult = Field(..., description="Quantum optimization result")
    value_at_risk: float = Field(..., description="Value at Risk")

class OptimizationJob(BaseModel):
    job_id: str = Field(..., description="Unique job identifier")
    status: str = Field(..., description="Job status: pending, running, completed, failed")
    created_at: datetime = Field(..., description="Job creation timestamp")
    completed_at: Optional[datetime] = Field(None, description="Job completion timestamp")
    result: Optional[Dict[str, Any]] = Field(None, description="Optimization result")
    error: Optional[str] = Field(None, description="Error message if failed")

# In-memory job storage (in production, use Redis or database)
job_store: Dict[str, OptimizationJob] = {}

# Server event handlers
@app.on_event("startup")
async def startup_event():
    """Server startup event handler."""
    logger.info("FastAPI server starting up...")
    
    # Test network connectivity to common addresses
    import socket
    addresses_to_test = [
        ("8.8.8.8", 53, "Google DNS"),
        ("1.1.1.1", 53, "Cloudflare DNS"),
        ("localhost", 8080, "Java Backend")
    ]
    
    for host, port, name in addresses_to_test:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(2)
            result = sock.connect_ex((host, port))
            sock.close()
            if result == 0:
                logger.info(f"Network connectivity to {name} ({host}:{port}): OK")
            else:
                logger.warning(f"Network connectivity to {name} ({host}:{port}): FAILED")
        except Exception as e:
            logger.warning(f"Network test to {name} ({host}:{port}): {str(e)}")
    
    # Test if required ports are available
    import socket
    ports_to_check = [8002]  # FastAPI server port
    
    for port in ports_to_check:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            sock.bind(('', port))
            logger.info(f"Port {port}: Available")
        except OSError:
            logger.warning(f"Port {port}: Already in use (this is expected if server is running)")
        finally:
            sock.close()
    
    logger.info("FastAPI server startup completed!")

@app.on_event("shutdown")
async def shutdown_event():
    """Server shutdown event handler."""
    logger.info("FastAPI server shutting down...")
    
    # Log final statistics
    total_jobs = len(job_store)
    completed_jobs = len([j for j in job_store.values() if j.status == "completed"])
    failed_jobs = len([j for j in job_store.values() if j.status == "failed"])
    
    uptime = datetime.now() - startup_time
    logger.info("Final statistics:")
    logger.info(f"  Uptime: {uptime}")
    logger.info(f"  Total jobs processed: {total_jobs}")
    logger.info(f"  Successful jobs: {completed_jobs}")
    logger.info(f"  Failed jobs: {failed_jobs}")
    
    logger.info("FastAPI server shutdown completed!")

# Middleware for request/response logging
@app.middleware("http")
async def log_requests(request, call_next):
    """Log all HTTP requests and responses."""
    request_id = str(uuid.uuid4())[:8]
    start_time = datetime.now()
    
    # Log request
    logger.info(f"[{request_id}] {request.method} {request.url.path} - Client: {request.client.host if request.client else 'unknown'}")
    
    # Process request
    try:
        response = await call_next(request)
        duration = (datetime.now() - start_time).total_seconds()
        
        # Log response
        logger.info(f"[{request_id}] Response: {response.status_code} - Duration: {duration:.3f}s")
        
        return response
        
    except Exception as e:
        duration = (datetime.now() - start_time).total_seconds()
        logger.error(f"[{request_id}] Request failed: {str(e)} - Duration: {duration:.3f}s")
        raise

# Utility functions
def convert_stock_data_to_dict(stock_data: List[StockDataPoint]) -> List[Dict[str, Any]]:
    """Convert Pydantic models to dictionary format expected by optimization functions."""
    return [
        {
            "symbol": point.symbol,
            "date": point.date,
            "close": point.close
        }
        for point in stock_data
    ]

def create_job(job_type: str) -> str:
    """Create a new optimization job and return job ID."""
    job_id = str(uuid.uuid4())
    job_store[job_id] = OptimizationJob(
        job_id=job_id,
        status="pending",
        created_at=datetime.now()
    )
    logger.info(f"Created {job_type} job: {job_id}")
    return job_id

def update_job_status(job_id: str, status: str, result: Optional[Dict] = None, error: Optional[str] = None):
    """Update job status and result."""
    if job_id in job_store:
        job = job_store[job_id]
        job.status = status
        if status in ["completed", "failed"]:
            job.completed_at = datetime.now()
        if result:
            job.result = result
        if error:
            job.error = error
        logger.info(f"Updated job {job_id}: status={status}")

# API Endpoints
@app.get("/health")
async def health_check():
    """Health check endpoint with detailed diagnostics."""
    try:
        logger.info("Health check requested")
        
        # Check system status
        import psutil
        cpu_percent = psutil.cpu_percent(interval=0.1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        # Check module availability
        modules_status = {}
        
        try:
            import pandas as pd
            modules_status['pandas'] = f"OK {pd.__version__}"
        except ImportError:
            modules_status['pandas'] = "Not available"
            
        try:
            import numpy as np
            modules_status['numpy'] = f"OK {np.__version__}"
        except ImportError:
            modules_status['numpy'] = "Not available"
            
        try:
            import pypfopt
            modules_status['pypfopt'] = f"OK {getattr(pypfopt, '__version__', 'unknown')}"
        except ImportError:
            modules_status['pypfopt'] = "Not available"
            
        try:
            import qiskit
            modules_status['qiskit'] = f"OK {qiskit.__version__}"
        except ImportError:
            modules_status['qiskit'] = "Not available"
        
        # Test optimization modules
        optimization_status = {}
        try:
            # Test classic optimization import
            from classic_portfolio_opt import optimize_portfolio
            optimization_status['classic_optimization'] = "Available"
        except ImportError as e:
            optimization_status['classic_optimization'] = f"Error: {str(e)}"
            
        try:
            # Test hybrid optimization import
            from hybrid_portfolio_opt import classical_optimize, quantum_optimize
            optimization_status['hybrid_optimization'] = "Available"
        except ImportError as e:
            optimization_status['hybrid_optimization'] = f"Error: {str(e)}"
        
        health_data = {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "service": "Quantum Portfolio Optimization API",
            "version": "1.0.0",
            "uptime_seconds": (datetime.now() - startup_time).total_seconds(),
            "system": {
                "cpu_percent": cpu_percent,
                "memory_percent": memory.percent,
                "memory_available_mb": memory.available // (1024*1024),
                "disk_free_gb": disk.free // (1024*1024*1024),
                "python_version": sys.version,
                "working_directory": os.getcwd()
            },
            "modules": modules_status,
            "optimization_engines": optimization_status,
            "endpoints": {
                "/health": "Active",
                "/api/optimize/classical": "Active", 
                "/api/optimize/hybrid": "Active",
                "/api/optimize/classical/async": "Active",
                "/api/optimize/hybrid/async": "Active",
                "/api/jobs/{job_id}": "Active",
                "/api/jobs": "Active"
            },
            "active_jobs": len(job_store),
            "completed_jobs": len([j for j in job_store.values() if j.status == "completed"]),
            "failed_jobs": len([j for j in job_store.values() if j.status == "failed"])
        }
        
        logger.info(f"Health check completed successfully - CPU: {cpu_percent}%, Memory: {memory.percent}%")
        return health_data
        
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        
        # Return basic health data even if detailed checks fail
        return {
            "status": "degraded",
            "timestamp": datetime.now().isoformat(),
            "service": "Quantum Portfolio Optimization API",
            "error": str(e),
            "basic_check": "API is responding but detailed diagnostics failed"
        }

@app.post("/api/optimize/classical", response_model=ClassicalResult)
async def optimize_classical(request: OptimizeRequest):
    """
    Perform classical portfolio optimization using Modern Portfolio Theory.
    """
    request_id = str(uuid.uuid4())[:8]
    logger.info(f"[{request_id}] Classical optimization request received")
    logger.info(f"[{request_id}] Request details: {len(request.stock_data)} stocks, VaR: {request.var_percent}")
    
    try:
        # Log stock symbols
        symbols = [point.symbol for point in request.stock_data]
        logger.info(f"[{request_id}] Stock symbols: {symbols}")
        
        # Convert request data
        stock_data_dict = convert_stock_data_to_dict(request.stock_data)
        logger.info(f"[{request_id}] Converted {len(stock_data_dict)} stock data points")
        
        # Validate we have stock data
        if not stock_data_dict or len(stock_data_dict) == 0:
            logger.error(f"[{request_id}] Empty stock data received")
            raise HTTPException(
                status_code=422,
                detail="stock_data cannot be empty"
            )
        
        # Perform optimization
        logger.info(f"[{request_id}] Starting classical optimization...")
        result = classic_optimize(stock_data_dict, request.var_percent)
        logger.info(f"[{request_id}] Classical optimization completed")
        
        # Log result summary
        if isinstance(result, dict) and 'weights' in result:
            logger.info(f"[{request_id}] Portfolio weights: {result.get('weights', {})}")
            logger.info(f"[{request_id}] Sharpe ratio: {result.get('sharpe_ratio', 'N/A')}")
        
        # Sanitize infinite values before returning
        sanitized_result = sanitize_infinite_values(result)
        
        logger.info(f"[{request_id}] Classical optimization completed successfully")
        return ClassicalResult(**sanitized_result)
        
    except HTTPException:
        # Re-raise HTTPException so it's not caught by the generic handler
        logger.warning(f"[{request_id}] HTTP exception raised")
        raise
    except Exception as e:
        logger.error(f"[{request_id}] Classical optimization failed: {str(e)}")
        logger.error(f"[{request_id}] Traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=500,
            detail=f"Classical optimization failed: {str(e)}"
        )

@app.post("/api/optimize/hybrid", response_model=HybridResult)
async def optimize_hybrid(request: OptimizeRequest):
    """
    Perform hybrid classical-quantum portfolio optimization.
    """
    request_id = str(uuid.uuid4())[:8]
    logger.info(f"[{request_id}] Hybrid optimization request received")
    logger.info(f"[{request_id}] Request details: {len(request.stock_data)} stocks, VaR: {request.var_percent}, QC Simulator: {request.qc_simulator}")
    
    try:
        # Log stock symbols
        symbols = [point.symbol for point in request.stock_data]
        logger.info(f"[{request_id}] Stock symbols: {symbols}")
        
        # Convert request data
        stock_data_dict = convert_stock_data_to_dict(request.stock_data)
        logger.info(f"[{request_id}] Converted {len(stock_data_dict)} stock data points")
        
        # Validate we have stock data
        if not stock_data_dict or len(stock_data_dict) == 0:
            logger.error(f"[{request_id}] Empty stock data received")
            raise HTTPException(
                status_code=422,
                detail="stock_data cannot be empty"
            )
        
        # Import pandas for data processing
        import pandas as pd
        
        # Prepare data
        logger.info(f"[{request_id}] Preparing data for optimization...")
        df = pd.DataFrame(stock_data_dict)
        prices = df.pivot(index='date', columns='symbol', values='close').sort_index()
        logger.info(f"[{request_id}] Data shape: {prices.shape} (dates × symbols)")
        
        # Classical optimization
        logger.info(f"[{request_id}] Running classical optimization...")
        classical_weights, classical_perf = classical_optimize(prices)
        logger.info(f"[{request_id}] Classical optimization completed")
        logger.info(f"[{request_id}] Classical weights: {classical_weights}")
        
        # Quantum optimization
        logger.info(f"[{request_id}] Running quantum optimization (simulator: {request.qc_simulator})...")
        # Set global simulator mode for hybrid_portfolio_opt module
        import hybrid_portfolio_opt
        hybrid_portfolio_opt.qc_simulator_mode = request.qc_simulator
        
        quantum_result = quantum_optimize(prices)
        logger.info(f"[{request_id}] Quantum optimization completed")
        logger.info(f"[{request_id}] Quantum result: {quantum_result}")
        
        # Prepare result
        result = {
            'classical_weights': classical_weights,
            'classical_performance': {
                'expected_annual_return': classical_perf[0],
                'annual_volatility': classical_perf[1],
                'sharpe_ratio': classical_perf[2]
            },
            'quantum_qaoa_result': quantum_result,
            'value_at_risk': request.var_percent
        }
        
        # Sanitize infinite values before returning
        sanitized_result = sanitize_infinite_values(result)
        
        logger.info(f"[{request_id}] Hybrid optimization completed successfully")
        return HybridResult(**sanitized_result)
        
    except HTTPException:
        # Re-raise HTTPException so it's not caught by the generic handler
        logger.warning(f"[{request_id}] HTTP exception raised")
        raise
    except Exception as e:
        logger.error(f"[{request_id}] Hybrid optimization failed: {str(e)}")
        logger.error(f"[{request_id}] Traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=500,
            detail=f"Hybrid optimization failed: {str(e)}"
        )

@app.post("/api/optimize/classical/async")
async def optimize_classical_async(request: OptimizeRequest, background_tasks: BackgroundTasks):
    """
    Start classical portfolio optimization as background task.
    Returns job ID for status tracking.
    """
    job_id = create_job("classical")
    background_tasks.add_task(run_classical_optimization, job_id, request)
    return {"job_id": job_id, "status": "pending"}

@app.post("/api/optimize/hybrid/async")
async def optimize_hybrid_async(request: OptimizeRequest, background_tasks: BackgroundTasks):
    """
    Start hybrid portfolio optimization as background task.
    Returns job ID for status tracking.
    """
    job_id = create_job("hybrid")
    background_tasks.add_task(run_hybrid_optimization, job_id, request)
    return {"job_id": job_id, "status": "pending"}

@app.get("/api/jobs/{job_id}")
async def get_job_status(job_id: str):
    """
    Get optimization job status and result.
    """
    if job_id not in job_store:
        raise HTTPException(status_code=404, detail="Job not found")
    
    job = job_store[job_id]
    return {
        "job_id": job.job_id,
        "status": job.status,
        "created_at": job.created_at.isoformat(),
        "completed_at": job.completed_at.isoformat() if job.completed_at else None,
        "result": job.result,
        "error": job.error
    }

@app.get("/api/jobs")
async def list_jobs():
    """
    List all optimization jobs.
    """
    return {
        "jobs": [
            {
                "job_id": job.job_id,
                "status": job.status,
                "created_at": job.created_at.isoformat(),
                "completed_at": job.completed_at.isoformat() if job.completed_at else None
            }
            for job in job_store.values()
        ]
    }

# Background task functions
def run_classical_optimization(job_id: str, request: OptimizeRequest):
    """Background task for classical optimization."""
    try:
        update_job_status(job_id, "running")
        
        stock_data_dict = convert_stock_data_to_dict(request.stock_data)
        result = classic_optimize(stock_data_dict, request.var_percent)
        
        update_job_status(job_id, "completed", result=result)
        
    except Exception as e:
        logger.error(f"Background classical optimization failed for job {job_id}: {str(e)}")
        update_job_status(job_id, "failed", error=str(e))

def run_hybrid_optimization(job_id: str, request: OptimizeRequest):
    """Background task for hybrid optimization."""
    try:
        update_job_status(job_id, "running")
        
        stock_data_dict = convert_stock_data_to_dict(request.stock_data)
        
        import pandas as pd
        df = pd.DataFrame(stock_data_dict)
        prices = df.pivot(index='date', columns='symbol', values='close').sort_index()
        
        # Set simulator mode
        import hybrid_portfolio_opt
        hybrid_portfolio_opt.qc_simulator_mode = request.qc_simulator
        
        classical_weights, classical_perf = classical_optimize(prices)
        quantum_result = quantum_optimize(prices)
        
        result = {
            'classical_weights': classical_weights,
            'classical_performance': {
                'expected_annual_return': classical_perf[0],
                'annual_volatility': classical_perf[1],
                'sharpe_ratio': classical_perf[2]
            },
            'quantum_qaoa_result': quantum_result,
            'value_at_risk': request.var_percent
        }
        
        update_job_status(job_id, "completed", result=result)
        
    except Exception as e:
        logger.error(f"Background hybrid optimization failed for job {job_id}: {str(e)}")
        update_job_status(job_id, "failed", error=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "portfolio_api:app",
        host="0.0.0.0",
        port=8002,
        reload=True,
        log_level="info"
    )