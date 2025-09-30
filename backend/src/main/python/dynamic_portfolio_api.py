"""
Dynamic Portfolio API Integration Module

Integrates the enhanced dynamic quantum portfolio optimization
with the existing FastAPI backend infrastructure.

This module provides:
1. REST API endpoints for dynamic optimization
2. Background task processing for long-running optimizations  
3. Configuration management and validation
4. Result caching and persistence
5. Performance monitoring and metrics
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Any
from pathlib import Path

import pandas as pd
import numpy as np
from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, validator
from sqlalchemy import Column, Integer, String, Float, DateTime, Text, Boolean
from sqlalchemy.ext.declarative import declarative_base

# Local imports
from enhanced_dynamic_portfolio_opt import (
    DynamicOptimizationConfig, 
    dynamic_quantum_optimize,
    OptimizationObjective
)

# Setup logging
logger = logging.getLogger(__name__)

# Database models
Base = declarative_base()

class OptimizationJob(Base):
    """Database model for tracking optimization jobs"""
    __tablename__ = "optimization_jobs"
    
    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(String(50), unique=True, index=True)
    user_id = Column(String(50), index=True)
    status = Column(String(20), default="pending")  # pending, running, completed, failed
    job_type = Column(String(30), default="dynamic_quantum")
    
    # Configuration
    config_json = Column(Text)
    assets = Column(Text)  # JSON list of asset symbols
    
    # Timing
    created_at = Column(DateTime, default=datetime.utcnow)
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    
    # Results
    result_json = Column(Text)
    objective_value = Column(Float)
    quantum_jobs_count = Column(Integer)
    
    # Metadata
    error_message = Column(Text)
    progress_percentage = Column(Float, default=0.0)


class OptimizationResult(Base):
    """Database model for storing optimization results"""
    __tablename__ = "optimization_results"
    
    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(String(50), index=True)
    time_step = Column(Integer)
    asset_symbol = Column(String(10))
    allocation_weight = Column(Float)
    expected_return = Column(Float)
    risk_contribution = Column(Float)
    
    created_at = Column(DateTime, default=datetime.utcnow)


# API request models
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
    previous_allocation: Optional[Dict[str, float]] = Field(None, description="Previous period allocations for transaction costs")
    
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

# Constants
JOB_NOT_FOUND_MESSAGE = "Job not found"

# In-memory job storage (replace with Redis in production)
active_jobs: Dict[str, Dict] = {}

@router.post("/optimize", response_model=Dict[str, str])
async def start_dynamic_optimization(
    request: DynamicOptimizationRequest,
    background_tasks: BackgroundTasks,
    user_id: str = "anonymous"
) -> Dict[str, str]:
    """
    Start dynamic portfolio optimization
    
    Args:
        request: Optimization configuration
        background_tasks: FastAPI background task handler
        user_id: User identifier
        
    Returns:
        Job ID for tracking optimization progress
    """
    try:
        # Generate unique job ID
        job_id = f"dpo_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}_{hash(str(request.dict()))}"
        
        logger.info(f"Starting dynamic optimization job {job_id}")
        
        # Validate asset data availability
        await _validate_asset_data(request.assets)
        
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
            background_tasks.add_task(_run_optimization_background, job_id, request)
            return {"job_id": job_id, "status": "queued"}
        else:
            # Run synchronously (with timeout protection)
            result = await _run_optimization_sync(job_id, request)
            return {"job_id": job_id, "status": "completed", "result": result}
            
    except Exception as e:
        logger.error(f"Failed to start optimization: {e}")
        raise HTTPException(status_code=400, detail=f"Optimization failed: {str(e)}")


@router.get("/status/{job_id}", response_model=OptimizationStatusResponse)
async def get_optimization_status(job_id: str) -> OptimizationStatusResponse:
    """
    Get status of optimization job
    
    Args:
        job_id: Optimization job identifier
        
    Returns:
        Job status information
    """
    if job_id not in active_jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    
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
    """
    Get optimization results
    
    Args:
        job_id: Optimization job identifier
        
    Returns:
        Optimization results and performance metrics
    """
    if job_id not in active_jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    job_data = active_jobs[job_id]
    
    if job_data["status"] != "completed":
        raise HTTPException(status_code=400, detail=f"Job status: {job_data['status']}")
    
    result = job_data.get("result", {})
    
    # Calculate additional performance metrics
    performance_metrics = _calculate_performance_metrics(result) if result else None
    
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
    limit: int = Field(50, description="Maximum number of jobs to return", ge=1, le=100)
) -> List[OptimizationStatusResponse]:
    """
    List optimization jobs with optional filtering
    
    Args:
        user_id: Filter by user ID
        status: Filter by job status
        limit: Maximum number of jobs to return
        
    Returns:
        List of job status information
    """
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
    """
    Cancel running optimization job
    
    Args:
        job_id: Job identifier to cancel
        
    Returns:
        Cancellation confirmation
    """
    if job_id not in active_jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    job_data = active_jobs[job_id]
    
    if job_data["status"] in ["completed", "failed", "cancelled"]:
        raise HTTPException(status_code=400, detail=f"Cannot cancel job with status: {job_data['status']}")
    
    # Mark as cancelled
    job_data["status"] = "cancelled"
    job_data["completed_at"] = datetime.utcnow()
    job_data["error_message"] = "Cancelled by user request"
    
    logger.info(f"Cancelled optimization job {job_id}")
    
    return {"message": f"Job {job_id} cancelled successfully"}


# Implementation functions
async def _validate_asset_data(assets: List[AssetConfig]) -> None:
    """
    Validate that price data is available for all requested assets
    
    Args:
        assets: List of asset configurations
        
    Raises:
        HTTPException: If asset data validation fails
    """
    # This is a placeholder - implement actual data validation
    # In production, check if historical price data exists for all symbols
    
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


async def _run_optimization_sync(job_id: str, request: DynamicOptimizationRequest) -> Dict:
    """
    Run optimization synchronously with timeout protection
    
    Args:
        job_id: Job identifier
        request: Optimization request
        
    Returns:
        Optimization result
    """
    try:
        # Update job status
        active_jobs[job_id]["status"] = "running"
        active_jobs[job_id]["started_at"] = datetime.utcnow()
        
        # Convert request to config
        config = _create_config_from_request(request)
        
        # Load price data
        prices_df = await _load_price_data([asset.symbol for asset in request.assets])
        
        # Convert previous allocation if provided
        prev_allocation = None
        if request.previous_allocation:
            prev_allocation = np.array([
                request.previous_allocation.get(asset.symbol, 0.0) 
                for asset in request.assets
            ])
        
        # Run optimization with timeout
        result = await asyncio.wait_for(
            _run_quantum_optimization(prices_df, config, prev_allocation),
            timeout=300.0  # 5 minute timeout
        )
        
        # Update job with results
        active_jobs[job_id]["status"] = "completed"
        active_jobs[job_id]["completed_at"] = datetime.utcnow()
        active_jobs[job_id]["result"] = result
        active_jobs[job_id]["progress"] = 100.0
        
        logger.info(f"Completed optimization job {job_id}")
        
        return result
        
    except asyncio.TimeoutError:
        active_jobs[job_id]["status"] = "failed"
        active_jobs[job_id]["error_message"] = "Optimization timeout"
        raise HTTPException(status_code=408, detail="Optimization timeout")
        
    except Exception as e:
        active_jobs[job_id]["status"] = "failed"
        active_jobs[job_id]["error_message"] = str(e)
        active_jobs[job_id]["completed_at"] = datetime.utcnow()
        logger.error(f"Optimization job {job_id} failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


async def _run_optimization_background(job_id: str, request: DynamicOptimizationRequest) -> None:
    """
    Run optimization in background task
    
    Args:
        job_id: Job identifier
        request: Optimization request
    """
    try:
        result = await _run_optimization_sync(job_id, request)
        logger.info(f"Background optimization {job_id} completed successfully")
        
    except Exception as e:
        logger.error(f"Background optimization {job_id} failed: {e}")


async def _run_quantum_optimization(prices_df: pd.DataFrame, 
                                  config: DynamicOptimizationConfig,
                                  previous_allocation: Optional[np.ndarray]) -> Dict:
    """
    Wrapper to run quantum optimization in async context
    
    Args:
        prices_df: Price data
        config: Optimization configuration
        previous_allocation: Previous period allocation
        
    Returns:
        Optimization result
    """
    # Run in thread pool since quantum optimization is CPU intensive
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(
        None, 
        dynamic_quantum_optimize,
        prices_df,
        config, 
        previous_allocation
    )


def _create_config_from_request(request: DynamicOptimizationRequest) -> DynamicOptimizationConfig:
    """
    Convert API request to optimization configuration
    
    Args:
        request: API request object
        
    Returns:
        Optimization configuration
    """
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


async def _load_price_data(asset_symbols: List[str]) -> pd.DataFrame:
    """
    Load historical price data for assets
    
    Args:
        asset_symbols: List of asset ticker symbols
        
    Returns:
        DataFrame with price data (dates × assets)
    """
    # Placeholder implementation - replace with actual data source
    # In production, integrate with yfinance, Alpha Vantage, or other provider
    
    logger.info(f"Loading price data for assets: {asset_symbols}")
    
    # Generate synthetic price data for testing
    np.random.seed(42)
    dates = pd.date_range('2023-01-01', periods=120, freq='D')
    
    price_data = {}
    rng = np.random.default_rng(seed=42)
    
    for symbol in asset_symbols:
        # Generate realistic price series
        returns = rng.normal(0.0008, 0.015, 120)  # Slightly positive mean return
        prices = 100 * np.exp(np.cumsum(returns))
        price_data[symbol] = prices
    
    return pd.DataFrame(price_data, index=dates)


def _calculate_performance_metrics(result: Dict) -> Dict[str, float]:
    """
    Calculate additional performance metrics from optimization result
    
    Args:
        result: Optimization result dictionary
        
    Returns:
        Performance metrics dictionary
    """
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
        logger.warning(f"Failed to calculate performance metrics: {e}")
        metrics["calculation_error"] = str(e)
    
    return metrics


# Health check endpoint
@router.get("/health")
async def health_check() -> Dict[str, str]:
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "dynamic-portfolio-optimization",
        "version": "1.0.0",
        "timestamp": datetime.utcnow().isoformat()
    }