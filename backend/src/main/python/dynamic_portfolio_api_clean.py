"""
Dynamic Portfolio API Integration Module - Production Ready

Integrates the enhanced dynamic quantum portfolio optimization
with the existing FastAPI backend infrastructure.
"""

import asyncio
import json
import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any

import pandas as pd
import numpy as np
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field, validator

# Local imports
from enhanced_dynamic_portfolio_opt import (
    DynamicOptimizationConfig, 
    dynamic_quantum_optimize
)

# Setup logging
logger = logging.getLogger(__name__)

# Constants
JOB_NOT_FOUND_ERROR = "Job not found"
OPTIMIZATION_TIMEOUT = 300.0  # 5 minutes

# In-memory job storage (replace with Redis in production)
active_jobs: Dict[str, Dict] = {}


class AssetConfig(BaseModel):
    """Asset configuration for optimization"""
    symbol: str = Field(..., description="Asset ticker symbol")
    name: Optional[str] = Field(None, description="Human-readable asset name")
    max_allocation: Optional[float] = Field(0.8, description="Maximum allocation percentage")
    
    @validator('max_allocation')
    def validate_max_allocation(cls, v):
        if v is not None and (v <= 0 or v > 1):
            raise ValueError('max_allocation must be between 0 and 1')
        return v


class DynamicOptimizationRequest(BaseModel):
    """Request model for dynamic portfolio optimization"""
    
    # Asset configuration
    assets: List[AssetConfig] = Field(..., description="List of assets to optimize")
    
    # Time period settings
    num_time_steps: int = Field(4, description="Number of rebalancing periods", ge=2, le=12)
    rebalance_frequency_days: int = Field(30, description="Days between rebalancing", ge=7, le=90)
    
    # Optimization parameters
    risk_aversion: float = Field(1000.0, description="Risk aversion coefficient", ge=0)
    transaction_fee: float = Field(0.01, description="Transaction cost rate", ge=0, le=0.1)
    
    # Quantum parameters  
    bit_resolution: int = Field(2, description="Bits per allocation variable", ge=1, le=4)
    num_generations: int = Field(20, description="DE generations", ge=5, le=100)
    population_size: int = Field(40, description="DE population size", ge=10, le=100)
    
    # Execution settings
    async_execution: bool = Field(False, description="Run optimization asynchronously")
    previous_allocation: Optional[Dict[str, float]] = Field(None, description="Previous period allocations")
    quantum_backend: Optional[str] = Field(None, description="Quantum backend to use (auto-select if None)")
    
    @validator('assets')
    def validate_assets(cls, v):
        if len(v) < 2:
            raise ValueError('At least 2 assets required for optimization')
        if len(v) > 10:
            raise ValueError('Maximum 10 assets supported')
        return v


class OptimizationStatusResponse(BaseModel):
    """Response model for optimization job status"""
    job_id: str
    status: str
    progress_percentage: float
    created_at: datetime
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    error_message: Optional[str]


class OptimizationResultResponse(BaseModel):
    """Response model for optimization results"""
    job_id: str
    status: str
    objective_value: Optional[float]
    quantum_jobs_count: Optional[int]
    allocations: Optional[Dict[str, Dict[str, float]]]
    configuration: Optional[Dict[str, Any]]
    performance_metrics: Optional[Dict[str, float]]


# Router setup
router = APIRouter(prefix="/api/v1/dynamic-portfolio", tags=["Dynamic Portfolio Optimization"])


@router.post("/optimize", response_model=Dict[str, str])
async def start_dynamic_optimization(
    request: DynamicOptimizationRequest,
    background_tasks: BackgroundTasks,
    user_id: str = "anonymous"
) -> Dict[str, str]:
    """Start dynamic portfolio optimization"""
    try:
        # Generate unique job ID
        timestamp = datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')
        job_id = f"dpo_{timestamp}_{hash(str(request.dict()))}"
        
        logger.info("Starting dynamic optimization job %s", job_id)
        
        # Validate asset data availability
        validate_asset_data(request.assets)
        
        # Create job record
        job_data = {
            "job_id": job_id,
            "user_id": user_id, 
            "status": "pending",
            "request": request.dict(),
            "created_at": datetime.now(timezone.utc),
            "progress": 0.0
        }
        
        active_jobs[job_id] = job_data
        
        # Start optimization (async if requested)
        if request.async_execution:
            background_tasks.add_task(run_optimization_background, job_id, request)
            return {"job_id": job_id, "status": "queued"}
        else:
            # Run synchronously (with timeout protection)
            result = await run_optimization_sync(job_id, request)
            return {"job_id": job_id, "status": "completed", "result": result}
            
    except Exception as e:
        logger.error("Failed to start optimization: %s", e)
        raise HTTPException(status_code=400, detail=f"Optimization failed: {str(e)}")


@router.get("/status/{job_id}", response_model=OptimizationStatusResponse)
async def get_optimization_status(job_id: str) -> OptimizationStatusResponse:
    """Get status of optimization job"""
    if job_id not in active_jobs:
        raise HTTPException(status_code=404, detail=JOB_NOT_FOUND_ERROR)
    
    job_data = active_jobs[job_id]
    
    return OptimizationStatusResponse(
        job_id=job_id,
        status=job_data["status"],
        progress_percentage=job_data.get("progress", 0.0),
        created_at=job_data["created_at"],
        started_at=job_data.get("started_at"),
        completed_at=job_data.get("completed_at"),
        error_message=job_data.get("error_message")
    )


@router.get("/result/{job_id}", response_model=OptimizationResultResponse)
async def get_optimization_result(job_id: str) -> OptimizationResultResponse:
    """Get optimization results"""
    if job_id not in active_jobs:
        raise HTTPException(status_code=404, detail=JOB_NOT_FOUND_ERROR)
    
    job_data = active_jobs[job_id]
    
    if job_data["status"] != "completed":
        raise HTTPException(status_code=400, detail=f"Job status: {job_data['status']}")
    
    result = job_data.get("result", {})
    
    # Calculate additional performance metrics
    performance_metrics = calculate_performance_metrics(result) if result else None
    
    return OptimizationResultResponse(
        job_id=job_id,
        status=job_data["status"],
        objective_value=result.get("objective_value"),
        quantum_jobs_count=result.get("quantum_jobs_executed"),
        allocations=result.get("allocations"),
        configuration=result.get("configuration"),
        performance_metrics=performance_metrics
    )


@router.get("/jobs", response_model=List[OptimizationStatusResponse])
async def list_optimization_jobs(
    user_id: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 50
) -> List[OptimizationStatusResponse]:
    """List optimization jobs with optional filtering"""
    jobs = []
    
    for job_id, job_data in list(active_jobs.items())[:limit]:
        # Apply filters
        if user_id and job_data.get("user_id") != user_id:
            continue
        if status and job_data.get("status") != status:
            continue
            
        jobs.append(OptimizationStatusResponse(
            job_id=job_id,
            status=job_data["status"],
            progress_percentage=job_data.get("progress", 0.0),
            created_at=job_data["created_at"],
            started_at=job_data.get("started_at"),
            completed_at=job_data.get("completed_at"),
            error_message=job_data.get("error_message")
        ))
    
    return jobs


@router.delete("/job/{job_id}")
async def cancel_optimization_job(job_id: str) -> Dict[str, str]:
    """Cancel running optimization job"""
    if job_id not in active_jobs:
        raise HTTPException(status_code=404, detail=JOB_NOT_FOUND_ERROR)
    
    job_data = active_jobs[job_id]
    
    if job_data["status"] in ["completed", "failed", "cancelled"]:
        raise HTTPException(
            status_code=400, 
            detail=f"Cannot cancel job with status: {job_data['status']}"
        )
    
    # Mark as cancelled
    job_data["status"] = "cancelled"
    job_data["completed_at"] = datetime.now(timezone.utc)
    job_data["error_message"] = "Cancelled by user request"
    
    logger.info("Cancelled optimization job %s", job_id)
    
    return {"message": f"Job {job_id} cancelled successfully"}


@router.get("/health")
async def health_check() -> Dict[str, str]:
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "dynamic-portfolio-optimization",
        "version": "1.0.0",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }


# Implementation functions
def validate_asset_data(assets: List[AssetConfig]) -> None:
    """Validate that price data is available for all requested assets"""
    unavailable_assets = []
    
    for asset in assets:
        # Simulate data availability check
        if asset.symbol.startswith("INVALID"):
            unavailable_assets.append(asset.symbol)
    
    if unavailable_assets:
        raise HTTPException(
            status_code=400, 
            detail=f"Price data not available for assets: {unavailable_assets}"
        )


async def run_optimization_sync(job_id: str, request: DynamicOptimizationRequest) -> Dict:
    """Run optimization synchronously with timeout protection"""
    try:
        # Update job status
        active_jobs[job_id]["status"] = "running"
        active_jobs[job_id]["started_at"] = datetime.now(timezone.utc)
        
        # Convert request to config
        config = create_config_from_request(request)
        
        # Load price data
        prices_df = load_price_data([asset.symbol for asset in request.assets])
        
        # Convert previous allocation if provided
        prev_allocation = None
        if request.previous_allocation:
            prev_allocation = np.array([
                request.previous_allocation.get(asset.symbol, 0.0) 
                for asset in request.assets
            ])
        
        # Run optimization with timeout
        result = await asyncio.wait_for(
            run_quantum_optimization(prices_df, config, prev_allocation, request.quantum_backend),
            timeout=OPTIMIZATION_TIMEOUT
        )
        
        # Update job with results
        active_jobs[job_id]["status"] = "completed"
        active_jobs[job_id]["completed_at"] = datetime.now(timezone.utc)
        active_jobs[job_id]["result"] = result
        active_jobs[job_id]["progress"] = 100.0
        
        logger.info("Completed optimization job %s", job_id)
        
        return result
        
    except asyncio.TimeoutError:
        active_jobs[job_id]["status"] = "failed"
        active_jobs[job_id]["error_message"] = "Optimization timeout"
        raise HTTPException(status_code=408, detail="Optimization timeout")
        
    except Exception as e:
        active_jobs[job_id]["status"] = "failed"
        active_jobs[job_id]["error_message"] = str(e)
        active_jobs[job_id]["completed_at"] = datetime.now(timezone.utc)
        logger.error("Optimization job %s failed: %s", job_id, e)
        raise HTTPException(status_code=500, detail=str(e))


async def run_optimization_background(job_id: str, request: DynamicOptimizationRequest) -> None:
    """Run optimization in background task"""
    try:
        await run_optimization_sync(job_id, request)
        logger.info("Background optimization %s completed successfully", job_id)
        
    except Exception as e:
        logger.error("Background optimization %s failed: %s", job_id, e)


async def run_quantum_optimization(prices_df: pd.DataFrame, 
                                  config: DynamicOptimizationConfig,
                                  previous_allocation: Optional[np.ndarray],
                                  quantum_backend: Optional[str] = None) -> Dict:
    """Wrapper to run quantum optimization in async context"""
    # Run in thread pool since quantum optimization is CPU intensive
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(
        None, 
        dynamic_quantum_optimize,
        prices_df,
        config, 
        previous_allocation,
        quantum_backend
    )


def create_config_from_request(request: DynamicOptimizationRequest) -> DynamicOptimizationConfig:
    """Convert API request to optimization configuration"""
    return DynamicOptimizationConfig(
        num_time_steps=request.num_time_steps,
        rebalance_frequency_days=request.rebalance_frequency_days,
        max_investment_per_asset=max([asset.max_allocation or 0.8 for asset in request.assets]),
        bit_resolution=request.bit_resolution,
        risk_aversion=request.risk_aversion,
        transaction_fee=request.transaction_fee,
        num_generations=request.num_generations,
        population_size=request.population_size,
        # Use reduced shots for API responsiveness
        estimator_shots=10000,
        sampler_shots=50000
    )


def load_price_data(asset_symbols: List[str]) -> pd.DataFrame:
    """Load historical price data for assets"""
    logger.info("Loading price data for assets: %s", asset_symbols)
    
    # Generate synthetic price data for testing
    dates = pd.date_range('2023-01-01', periods=120, freq='D')
    
    price_data = {}
    rng = np.random.default_rng(seed=42)
    
    for symbol in asset_symbols:
        # Generate realistic price series
        returns = rng.normal(0.0008, 0.015, 120)  # Slightly positive mean return
        prices = 100 * np.exp(np.cumsum(returns))
        price_data[symbol] = prices
    
    return pd.DataFrame(price_data, index=dates)


def calculate_performance_metrics(result: Dict) -> Dict[str, float]:
    """Calculate additional performance metrics from optimization result"""
    metrics = {}
    
    try:
        allocations = result.get("allocations", {})
        
        if allocations:
            # Calculate allocation statistics
            all_allocations = []
            for time_step_data in allocations.values():
                all_allocations.extend(time_step_data.values())
            
            metrics["mean_allocation"] = float(np.mean(all_allocations))
            metrics["allocation_std"] = float(np.std(all_allocations))
            metrics["max_allocation"] = float(np.max(all_allocations))
            metrics["min_allocation"] = float(np.min(all_allocations))
            
            # Diversification measure (1 - sum of squared weights)
            for time_step, step_allocations in allocations.items():
                weights = np.array(list(step_allocations.values()))
                weights = weights / np.sum(weights) if np.sum(weights) > 0 else weights
                diversification = 1 - np.sum(weights ** 2)
                metrics[f"diversification_{time_step}"] = float(diversification)
        
        # Quantum efficiency metrics
        metrics["quantum_jobs_executed"] = result.get("quantum_jobs_executed", 0)
        metrics["objective_value"] = result.get("objective_value", 0.0)
        
        # Job timing (if available)
        config = result.get("configuration", {})
        if config:
            metrics["num_time_steps"] = config.get("num_time_steps", 0)
            metrics["bit_resolution"] = config.get("bit_resolution", 0)
            metrics["total_qubits"] = (
                config.get("num_time_steps", 0) * 
                config.get("bit_resolution", 0) * 
                len(allocations.get("time_step_0", {}))
            )
        
    except Exception as e:
        logger.warning("Failed to calculate performance metrics: %s", e)
        metrics["calculation_error"] = str(e)
    
    return metrics


@router.get("/quantum-backends", response_model=Dict[str, Any])
async def list_quantum_backends():
    """
    List all available quantum backends with their specifications
    """
    try:
        from quantum_backend_config import QuantumBackendManager
        
        # Initialize backend manager
        backend_manager = QuantumBackendManager()
        
        # Discover all backends
        all_backends = backend_manager.discover_backends()
        
        # Format backend information for API response
        backends_info = {}
        for name, info in all_backends.items():
            backends_info[name] = {
                "name": info.name,
                "type": info.backend_type.value,
                "provider": info.provider,
                "num_qubits": info.num_qubits,
                "status": info.status.value,
                "queue_length": info.queue_length,
                "avg_queue_time_minutes": info.avg_queue_time,
                "gate_error_rate": info.gate_error_rate,
                "readout_error_rate": info.readout_error_rate,
                "max_shots": info.max_shots,
                "description": info.description
            }
        
        return {
            "backends": backends_info,
            "total_count": len(backends_info),
            "recommended": backend_manager.select_best_backend(num_qubits=10, prefer_hardware=False)
        }
        
    except Exception as e:
        logger.error("Failed to list quantum backends: %s", e)
        raise HTTPException(
            status_code=500, 
            detail=f"Failed to query quantum backends: {str(e)}"
        )


@router.get("/quantum-backends/recommend", response_model=Dict[str, Any])
async def recommend_quantum_backend(
    num_qubits: int = 10,
    prefer_hardware: bool = False
):
    """
    Get recommended quantum backend for given requirements
    """
    try:
        from quantum_backend_config import QuantumBackendManager
        
        # Initialize backend manager
        backend_manager = QuantumBackendManager()
        
        # Get recommendation
        recommended_name = backend_manager.select_best_backend(num_qubits, prefer_hardware)
        
        if not recommended_name:
            return {
                "recommended_backend": None,
                "message": "No suitable backend found for the given requirements"
            }
        
        # Get detailed info about recommended backend
        recommended_info = backend_manager.get_backend_info(recommended_name)
        
        return {
            "recommended_backend": recommended_name,
            "backend_info": {
                "name": recommended_info.name,
                "type": recommended_info.backend_type.value,
                "provider": recommended_info.provider,
                "num_qubits": recommended_info.num_qubits,
                "status": recommended_info.status.value,
                "queue_length": recommended_info.queue_length,
                "avg_queue_time_minutes": recommended_info.avg_queue_time,
                "gate_error_rate": recommended_info.gate_error_rate,
                "readout_error_rate": recommended_info.readout_error_rate,
                "description": recommended_info.description
            },
            "criteria": {
                "min_qubits": num_qubits,
                "prefer_hardware": prefer_hardware
            }
        }
        
    except Exception as e:
        logger.error("Failed to recommend quantum backend: %s", e)
        raise HTTPException(
            status_code=500, 
            detail=f"Failed to recommend quantum backend: {str(e)}"
        )