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
try:
    from classic_portfolio_opt import optimize_portfolio as classic_optimize
except ImportError:
    # Fallback import approach
    import sys
    import os
    sys.path.append(os.path.dirname(__file__))
    from classic_portfolio_opt import optimize_portfolio as classic_optimize

try:
    from hybrid_portfolio_opt import classical_optimize, quantum_optimize
except ImportError:
    from hybrid_portfolio_opt import classical_optimize, quantum_optimize

# Configure logging
logging.basicConfig(level=logging.INFO)
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
    """Health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "service": "Quantum Portfolio Optimization API"
    }

@app.post("/api/optimize/classical", response_model=ClassicalResult)
async def optimize_classical(request: OptimizeRequest):
    """
    Perform classical portfolio optimization using Modern Portfolio Theory.
    """
    try:
        logger.info("Starting classical portfolio optimization")
        
        # Convert request data
        stock_data_dict = convert_stock_data_to_dict(request.stock_data)
        
        # Validate we have stock data
        if not stock_data_dict or len(stock_data_dict) == 0:
            raise HTTPException(
                status_code=422,
                detail="stock_data cannot be empty"
            )
        
        # Perform optimization
        result = classic_optimize(stock_data_dict, request.var_percent)
        
        # Sanitize infinite values before returning
        sanitized_result = sanitize_infinite_values(result)
        
        logger.info("Classical optimization completed successfully")
        return ClassicalResult(**sanitized_result)
        
    except HTTPException:
        # Re-raise HTTPException so it's not caught by the generic handler
        raise
    except Exception as e:
        logger.error(f"Classical optimization failed: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=500,
            detail=f"Classical optimization failed: {str(e)}"
        )

@app.post("/api/optimize/hybrid", response_model=HybridResult)
async def optimize_hybrid(request: OptimizeRequest):
    """
    Perform hybrid classical-quantum portfolio optimization.
    """
    try:
        logger.info(f"Starting hybrid optimization (simulator: {request.qc_simulator})")
        
        # Convert request data
        stock_data_dict = convert_stock_data_to_dict(request.stock_data)
        
        # Validate we have stock data
        if not stock_data_dict or len(stock_data_dict) == 0:
            raise HTTPException(
                status_code=422,
                detail="stock_data cannot be empty"
            )
        
        # Import pandas for data processing
        import pandas as pd
        
        # Prepare data
        df = pd.DataFrame(stock_data_dict)
        prices = df.pivot(index='date', columns='symbol', values='close').sort_index()
        
        # Classical optimization
        logger.info("Running classical optimization...")
        classical_weights, classical_perf = classical_optimize(prices)
        
        # Quantum optimization
        logger.info("Running quantum optimization...")
        # Set global simulator mode for hybrid_portfolio_opt module
        import hybrid_portfolio_opt
        hybrid_portfolio_opt.qc_simulator_mode = request.qc_simulator
        
        quantum_result = quantum_optimize(prices)
        
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
        
        logger.info("Hybrid optimization completed successfully")
        return HybridResult(**sanitized_result)
        
    except HTTPException:
        # Re-raise HTTPException so it's not caught by the generic handler
        raise
    except Exception as e:
        logger.error(f"Hybrid optimization failed: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
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
        port=8001,
        reload=True,
        log_level="info"
    )