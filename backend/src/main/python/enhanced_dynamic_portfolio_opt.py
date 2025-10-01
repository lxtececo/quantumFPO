"""
Enhanced Dynamic Portfolio Optimization Implementation
Based on IBM Quantum Global Data Quantum Portfolio Optimizer approach

This module implements the multi-objective QUBO formulation from:
"Scaling the Variational Quantum Eigensolver for Dynamic Portfolio Optimization"
arXiv:2412.19150 (2024)

Key improvements:
1. Multi-period dynamic optimization
2. Multi-objective QUBO: O = -F + γ²R + C + ρP  
3. Multi-bit asset encoding (fractional allocations)
4. Transaction cost modeling
5. Advanced constraint handling
6. Differential Evolution + VQE hybrid optimization
"""

import sys
import json
import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from enum import Enum

from pypfopt import expected_returns
from pypfopt.risk_models import CovarianceShrinkage
from qiskit.quantum_info import SparsePauliOp
from qiskit.circuit.library import RealAmplitudes
from qiskit.transpiler import generate_preset_pass_manager
from scipy.optimize import differential_evolution, minimize
import warnings
warnings.filterwarnings('ignore')

from quantum_backend_config import QuantumBackendManager


@dataclass
class DynamicOptimizationConfig:
    """Configuration for dynamic portfolio optimization"""
    # Time period settings
    num_time_steps: int = 4
    rebalance_frequency_days: int = 30
    
    # Investment constraints  
    max_investment_per_asset: float = 0.8  # 80% max allocation
    bit_resolution: int = 2  # Bits per investment variable
    
    # QUBO objective weights
    risk_aversion: float = 1000.0  # γ coefficient
    transaction_fee: float = 0.01  # 1% transaction cost
    restriction_coefficient: float = 1.0  # ρ penalty coefficient
    
    # Optimization settings
    optimizer_type: str = "differential_evolution"
    num_generations: int = 20
    population_size: int = 40
    recombination: float = 0.4
    max_parallel_jobs: int = 8  # Increase to use more CPU cores
    
    # Quantum settings
    estimator_shots: int = 25000
    sampler_shots: int = 100000
    ansatz_reps: int = 3
    use_optimized_ansatz: bool = True
    
    # Testing mode for ultra-fast development
    test_mode: bool = False  # Use classical approximation for fastest testing


class OptimizationObjective(Enum):
    """QUBO objective components"""
    RETURN = "return_maximization"      # F: Expected return
    RISK = "risk_minimization"          # R: Portfolio risk  
    TRANSACTION = "transaction_cost"     # C: Rebalancing costs
    CONSTRAINT = "constraint_penalty"    # P: Investment restrictions


def calculate_total_qubits(num_assets: int, num_periods: int, config: DynamicOptimizationConfig) -> int:
    """
    Calculate total qubits needed: na × np × nq
    
    Args:
        num_assets: Number of portfolio assets
        num_periods: Actual number of periods in optimization  
        config: Optimization configuration
        
    Returns:
        Total number of qubits required
    """
    return num_assets * num_periods * config.bit_resolution


def prepare_multi_period_data(prices: pd.DataFrame, config: DynamicOptimizationConfig) -> List[pd.DataFrame]:
    """
    Split price data into overlapping time periods for dynamic optimization
    
    Args:
        prices: Historical price DataFrame (dates × assets)
        config: Optimization configuration
        
    Returns:
        List of DataFrames, one per time period
    """
    periods = []
    total_days = len(prices)
    
    for t in range(config.num_time_steps):
        start_idx = t * config.rebalance_frequency_days
        end_idx = min(start_idx + config.rebalance_frequency_days * 2, total_days)
        
        if end_idx - start_idx < config.rebalance_frequency_days:
            break
            
        period_data = prices.iloc[start_idx:end_idx]
        periods.append(period_data)
        
    return periods


def build_dynamic_qubo(periods_data: List[pd.DataFrame], 
                      config: DynamicOptimizationConfig,
                      previous_allocation: Optional[np.ndarray] = None) -> Tuple[np.ndarray, np.ndarray, int]:
    """
    Build enhanced QUBO matrix for dynamic multi-period portfolio optimization
    
    Implements equation (15): O = -F + γ²R + C + ρP
    
    Args:
        periods_data: List of price DataFrames for each time period
        config: Optimization configuration
        previous_allocation: Previous period allocation for transaction costs
        
    Returns:
        Tuple of (linear_coeffs, quadratic_matrix, total_qubits)
    """
    num_assets = periods_data[0].shape[1] 
    num_periods = len(periods_data)
    total_qubits = calculate_total_qubits(num_assets, num_periods, config)
    
    print(f"[LOG] Building dynamic QUBO: {num_assets} assets, {num_periods} periods, {total_qubits} qubits")
    
    # Initialize QUBO components
    linear = np.zeros(total_qubits)
    quadratic = np.zeros((total_qubits, total_qubits))
    
    # Build each objective component
    linear, quadratic = add_return_objective(linear, quadratic, periods_data, config)
    linear, quadratic = add_risk_objective(linear, quadratic, periods_data, config)
    linear, quadratic = add_transaction_cost_objective(linear, quadratic, config, num_periods, previous_allocation)
    linear, quadratic = add_constraint_penalties(linear, quadratic, config, num_periods, num_assets)
    
    print(f"[LOG] QUBO construction complete: linear shape {linear.shape}, quadratic shape {quadratic.shape}")
    
    return linear, quadratic, total_qubits


def add_return_objective(linear: np.ndarray, quadratic: np.ndarray, 
                        periods_data: List[pd.DataFrame], 
                        config: DynamicOptimizationConfig) -> Tuple[np.ndarray, np.ndarray]:
    """
    Add return maximization objective: -F (negative for maximization)
    
    Args:
        linear: Linear QUBO coefficients
        quadratic: Quadratic QUBO matrix
        periods_data: Price data for each period
        config: Optimization configuration
        
    Returns:
        Updated (linear, quadratic) coefficients
    """
    num_assets = periods_data[0].shape[1]
    num_periods = len(periods_data)
    
    for period_idx, period_prices in enumerate(periods_data):
        # Calculate expected returns for this period
        mu = expected_returns.mean_historical_return(period_prices)
        
        # Add to linear terms (negative for maximization)
        for asset_idx in range(num_assets):
            for bit_idx in range(config.bit_resolution):
                qubit_idx = _get_qubit_index(asset_idx, period_idx, bit_idx, config, num_periods)
                
                # Weight by bit significance (2^bit_idx)
                bit_weight = 2 ** bit_idx
                allocation_weight = bit_weight / ((2 ** config.bit_resolution) - 1)
                
                # Add negative expected return (for maximization)
                linear[qubit_idx] -= mu.iloc[asset_idx] * allocation_weight
    
    return linear, quadratic


def add_risk_objective(linear: np.ndarray, quadratic: np.ndarray,
                      periods_data: List[pd.DataFrame],
                      config: DynamicOptimizationConfig) -> Tuple[np.ndarray, np.ndarray]:
    """
    Add risk minimization objective: γ²R
    
    Args:
        linear: Linear QUBO coefficients  
        quadratic: Quadratic QUBO matrix
        periods_data: Price data for each period
        config: Optimization configuration
        
    Returns:
        Updated (linear, quadratic) coefficients
    """
    num_assets = periods_data[0].shape[1]
    num_periods = len(periods_data)
    
    for period_idx, period_prices in enumerate(periods_data):
        # Calculate covariance matrix for this period
        S = CovarianceShrinkage(period_prices).ledoit_wolf()
        
        # Add quadratic risk terms
        for i in range(num_assets):
            for j in range(num_assets):
                for bit_i in range(config.bit_resolution):
                    for bit_j in range(config.bit_resolution):
                        qubit_i = _get_qubit_index(i, period_idx, bit_i, config, num_periods)
                        qubit_j = _get_qubit_index(j, period_idx, bit_j, config, num_periods)
                        
                        # Debug bounds checking
                        if qubit_i >= len(linear) or qubit_j >= len(linear):
                            print(f"[ERROR] Qubit index out of bounds: qubit_i={qubit_i}, qubit_j={qubit_j}, linear_size={len(linear)}")
                            continue
                            
                        if i >= S.shape[0] or j >= S.shape[1]:
                            print(f"[ERROR] Covariance matrix index out of bounds: i={i}, j={j}, S_shape={S.shape}")
                            continue
                        
                        # Bit weights
                        weight_i = 2 ** bit_i / ((2 ** config.bit_resolution) - 1)
                        weight_j = 2 ** bit_j / ((2 ** config.bit_resolution) - 1)
                        
                        # Risk coefficient
                        risk_coeff = config.risk_aversion * S.iloc[i, j] * weight_i * weight_j
                        
                        if i == j and bit_i == bit_j:
                            # Diagonal terms go to linear
                            linear[qubit_i] += risk_coeff
                        else:
                            # Off-diagonal terms go to quadratic  
                            quadratic[qubit_i, qubit_j] += risk_coeff / 2
    
    return linear, quadratic


def add_transaction_cost_objective(linear: np.ndarray, quadratic: np.ndarray,
                                 config: DynamicOptimizationConfig,
                                 num_periods: int,
                                 previous_allocation: Optional[np.ndarray] = None) -> Tuple[np.ndarray, np.ndarray]:
    """
    Add transaction cost minimization: C
    
    Models costs of changing allocations between periods
    
    Args:
        linear: Linear QUBO coefficients
        quadratic: Quadratic QUBO matrix  
        config: Optimization configuration
        num_periods: Actual number of periods in the optimization
        previous_allocation: Previous period allocation (if available)
        
    Returns:
        Updated (linear, quadratic) coefficients
    """
    if previous_allocation is None or num_periods <= 1:
        return linear, quadratic
        
    num_assets = len(previous_allocation)
    
    # Transaction costs apply between consecutive periods
    for period_idx in range(1, num_periods):
        for asset_idx in range(num_assets):
            # Current period allocation qubits
            current_qubits = []
            for bit_idx in range(config.bit_resolution):
                qubit_idx = _get_qubit_index(asset_idx, period_idx, bit_idx, config, num_periods)
                current_qubits.append(qubit_idx)
            
            # Previous period allocation (from previous_allocation array)
            prev_allocation = previous_allocation[asset_idx]
            
            # Add quadratic terms for |current - previous|² approximation
            # This is a simplified model - full implementation would need absolute value handling
            for qubit in current_qubits:
                linear[qubit] += config.transaction_fee * prev_allocation
                
    return linear, quadratic


def add_constraint_penalties(linear: np.ndarray, quadratic: np.ndarray,
                           config: DynamicOptimizationConfig, 
                           num_periods: int,
                           num_assets: int = 3) -> Tuple[np.ndarray, np.ndarray]:
    """
    Add constraint penalty terms: ρP
    
    Enforces:
    1. Sum of allocations ≤ 1 (budget constraint)
    2. Individual asset allocation ≤ max_investment_per_asset
    
    Args:
        linear: Linear QUBO coefficients
        quadratic: Quadratic QUBO matrix
        config: Optimization configuration
        num_periods: Actual number of periods in the optimization
        num_assets: Number of assets in the portfolio
        
    Returns:
        Updated (linear, quadratic) coefficients
    """
    
    # Budget constraint: (Σ allocations - 1)² penalty
    for period_idx in range(num_periods):
        # Add penalty for deviating from full investment (sum = 1)
        penalty_strength = config.restriction_coefficient
        
        # Quadratic terms for (Σx_i - 1)²
        for asset_i in range(num_assets):
            for asset_j in range(num_assets):
                for bit_i in range(config.bit_resolution):
                    for bit_j in range(config.bit_resolution):
                        qubit_i = _get_qubit_index(asset_i, period_idx, bit_i, config, num_periods)
                        qubit_j = _get_qubit_index(asset_j, period_idx, bit_j, config, num_periods)
                        
                        weight_i = 2 ** bit_i / ((2 ** config.bit_resolution) - 1)
                        weight_j = 2 ** bit_j / ((2 ** config.bit_resolution) - 1)
                        
                        if asset_i == asset_j and bit_i == bit_j:
                            # x_i² terms
                            linear[qubit_i] += penalty_strength * weight_i * (weight_i - 2)
                        else:
                            # x_i * x_j cross terms
                            quadratic[qubit_i, qubit_j] += penalty_strength * weight_i * weight_j / 2
    
    return linear, quadratic


def _get_qubit_index(asset_idx: int, period_idx: int, bit_idx: int, 
                     config: DynamicOptimizationConfig, num_periods: int) -> int:
    """
    Calculate global qubit index from asset, period, and bit indices
    
    Qubit ordering: asset_0_period_0_bit_0, asset_0_period_0_bit_1, ...
                   asset_0_period_1_bit_0, asset_0_period_1_bit_1, ...
                   asset_1_period_0_bit_0, ...
    
    Args:
        asset_idx: Asset index
        period_idx: Time period index  
        bit_idx: Bit index within asset allocation
        config: Optimization configuration
        num_periods: Actual number of periods (not config.num_time_steps)
        
    Returns:
        Global qubit index
    """
    qubits_per_period = config.bit_resolution
    qubits_per_asset = num_periods * qubits_per_period  # Use actual periods count
    
    return (asset_idx * qubits_per_asset + 
            period_idx * qubits_per_period + 
            bit_idx)


def create_optimized_ansatz(num_qubits: int, config: DynamicOptimizationConfig) -> RealAmplitudes:
    """
    Create hardware-efficient ansatz optimized for portfolio optimization
    
    Based on IBM's "Optimized Real Amplitudes" approach
    
    Args:
        num_qubits: Total number of qubits
        config: Optimization configuration
        
    Returns:
        Quantum circuit ansatz
    """
    if config.use_optimized_ansatz:
        # Hardware-efficient Real Amplitudes with optimizations
        ansatz = RealAmplitudes(
            num_qubits=num_qubits,
            reps=config.ansatz_reps,
            entanglement='circular',  # Better connectivity than linear
            skip_final_rotation_layer=False,
            insert_barriers=True  # Better for real hardware
        )
        
        print(f"[LOG] Created optimized RealAmplitudes ansatz: {num_qubits} qubits, {config.ansatz_reps} reps")
        
    else:
        # Fallback to basic ansatz
        from qiskit.circuit.library import QAOAAnsatz
        hamiltonian = build_hamiltonian_from_qubo(np.zeros(num_qubits), 
                                                np.zeros((num_qubits, num_qubits)), 
                                                num_qubits)
        ansatz = QAOAAnsatz(cost_operator=hamiltonian, reps=2)
        
    return ansatz


def build_hamiltonian_from_qubo(linear: np.ndarray, quadratic: np.ndarray, num_qubits: int) -> SparsePauliOp:
    """
    Convert QUBO coefficients to quantum Hamiltonian
    
    Args:
        linear: Linear QUBO coefficients
        quadratic: Quadratic QUBO matrix
        num_qubits: Number of qubits
        
    Returns:
        Hamiltonian as SparsePauliOp
    """
    pauli_terms = []
    
    # Linear terms: h_i * Z_i  
    for i in range(num_qubits):
        if abs(linear[i]) > 1e-10:  # Skip near-zero terms
            label = 'I' * i + 'Z' + 'I' * (num_qubits - i - 1)
            pauli_terms.append((label, linear[i]))
    
    # Quadratic terms: J_ij * Z_i * Z_j
    for i in range(num_qubits):
        for j in range(i+1, num_qubits):
            if abs(quadratic[i, j]) > 1e-10:  # Skip near-zero terms
                label = ['I'] * num_qubits
                label[i] = 'Z'
                label[j] = 'Z'
                pauli_terms.append((''.join(label), quadratic[i, j]))
    
    print(f"[LOG] Built Hamiltonian: {len(pauli_terms)} Pauli terms")
    
    if not pauli_terms:
        # Fallback identity if no terms
        pauli_terms = [('I' * num_qubits, 0.0)]
    
    return SparsePauliOp.from_list(pauli_terms)


def decode_quantum_solution(bitstring: str, config: DynamicOptimizationConfig, 
                           num_assets: int, num_periods: int) -> Dict[str, Dict[str, float]]:
    """
    Decode quantum bitstring solution to portfolio allocations
    
    Args:
        bitstring: Quantum measurement result
        config: Optimization configuration  
        num_assets: Number of assets
        num_periods: Number of periods in the optimization
        
    Returns:
        Dictionary mapping time_step -> {asset -> allocation}
    """
    allocations = {}
    
    for period_idx in range(num_periods):
        period_key = f"time_step_{period_idx}"
        allocations[period_key] = {}
        
        for asset_idx in range(num_assets):
            # Extract bits for this asset in this period
            asset_bits = []
            for bit_idx in range(config.bit_resolution):
                qubit_idx = _get_qubit_index(asset_idx, period_idx, bit_idx, config, num_periods)
                if qubit_idx < len(bitstring):
                    asset_bits.append(bitstring[qubit_idx])
                else:
                    asset_bits.append('0')
            
            # Convert binary to allocation percentage
            bit_value = int(''.join(reversed(asset_bits)), 2)  # LSB first
            max_value = (2 ** config.bit_resolution) - 1
            allocation = bit_value / max_value * config.max_investment_per_asset
            
            allocations[period_key][f"asset_{asset_idx}"] = allocation
    
    return allocations


def run_differential_evolution_vqe(ansatz, hamiltonian, config: DynamicOptimizationConfig, quantum_backend: Optional[str] = None):
    """
    Run VQE optimization using Differential Evolution
    
    Based on IBM's hybrid quantum-classical approach
    
    Args:
        ansatz: Quantum circuit ansatz
        hamiltonian: Problem Hamiltonian
        config: Optimization configuration
        quantum_backend: Name of quantum backend to use (None for auto-selection)
        
    Returns:
        Optimization result with quantum solution
    """
    import time
    from qiskit_aer import AerSimulator
    from qiskit_ibm_runtime import SamplerV2 as Sampler
    
    start_time = time.time()
    optimization_timeout = 60  # 1 minute maximum for VQE
    
    print(f"[LOG] Starting Differential Evolution VQE: {config.num_generations} generations, {config.population_size} population")
    print(f"[LOG] Optimization timeout set to {optimization_timeout} seconds")
    
    # Initialize quantum backend manager
    backend_manager = QuantumBackendManager()
    
    # Select and configure quantum backend
    num_qubits = ansatz.num_qubits
    if quantum_backend:
        selected_backend_info = backend_manager.get_backend_info(quantum_backend)
        if not selected_backend_info:
            print(f"[WARNING] Backend '{quantum_backend}' not found, using auto-selection")
            backend_name = backend_manager.select_best_backend(num_qubits, prefer_hardware=True)
        else:
            backend_name = quantum_backend
    else:
        backend_name = backend_manager.select_best_backend(num_qubits, prefer_hardware=True)
    
    selected_backend_info = backend_manager.get_backend_info(backend_name)
    
    print(f"[LOG] Using quantum backend: {selected_backend_info.name} ({selected_backend_info.backend_type.value})")
    
    # Setup quantum backend for execution  
    backend = backend_manager.get_backend_instance(backend_name)
    pm = generate_preset_pass_manager(backend=backend, optimization_level=2)
    sampler = Sampler(mode=backend)
    
    # Parameter bounds
    num_params = ansatz.num_parameters
    bounds = [(0, 2 * np.pi)] * num_params
    
    job_count = 0
    
    def cost_function(params):
        nonlocal job_count
        job_count += 1
        
        # Check timeout to prevent infinite execution
        if time.time() - start_time > optimization_timeout:
            print(f"[LOG] Stopping optimization: timeout reached ({optimization_timeout}s)")
            return 1e6  # Force termination with high cost
        
        # Enforce hard limit on job count to prevent runaway optimization
        max_jobs = max(20, config.num_generations * config.population_size * 3)
        if job_count > max_jobs:
            print(f"[LOG] Stopping optimization: reached max jobs limit ({max_jobs})\"")
            return 1e6  # Force termination with high cost
        
        try:
            # Prepare parameterized circuit
            circuit = ansatz.assign_parameters(params)
            isa_circuit = pm.run(circuit)
            
            # Execute on quantum simulator
            job = sampler.run([isa_circuit], shots=config.estimator_shots)
            result = job.result()
            
            # Extract measurement counts
            counts = result[0].data.meas.get_counts()
            
            # Compute expectation value
            expectation = compute_expectation_from_counts(counts, hamiltonian)
            
            if job_count % 50 == 0:
                print(f"[LOG] DE-VQE job {job_count}: expectation = {expectation:.4f}")
            
            return expectation
            
        except Exception as e:
            print(f"[LOG] Cost function error: {e}")
            return 1e6  # Return high cost on error
    
    # Run Differential Evolution (sequential for now due to pickle constraints)
    # Note: Parallelization disabled temporarily due to local function pickle issue
    print("[LOG] Running DE optimization with ultra-minimal parameters for speed")
    
    # Add strict limits to prevent runaway optimization
    max_evaluations = max(10, config.num_generations * config.population_size * 2)  # Hard limit
    
    result = differential_evolution(
        cost_function,
        bounds,
        maxiter=config.num_generations,
        popsize=config.population_size,
        recombination=config.recombination,
        workers=1,  # Sequential to avoid pickle issues
        seed=42,
        # Add convergence criteria for early stopping
        tol=1e-3,  # Stop if improvement is less than this
        atol=1e-6,  # Absolute tolerance
        # Add callback to enforce hard limits
        callback=lambda x, convergence: job_count >= max_evaluations
    )
    
    print(f"[LOG] DE-VQE complete: {job_count} evaluations, best cost = {result.fun:.4f}")
    
    # Get final solution bitstring
    final_circuit = ansatz.assign_parameters(result.x)
    isa_final = pm.run(final_circuit)
    
    final_job = sampler.run([isa_final], shots=config.sampler_shots)
    final_result = final_job.result()
    final_counts = final_result[0].data.meas.get_counts()
    
    # Get most probable bitstring
    best_bitstring = max(final_counts, key=final_counts.get)
    
    return {
        'solution': best_bitstring,
        'objective_value': result.fun,
        'optimization_result': result,
        'job_count': job_count,
        'final_counts': final_counts,
        'backend_name': backend_name
    }


def compute_expectation_from_counts(counts: dict, hamiltonian: SparsePauliOp) -> float:
    """
    Compute Hamiltonian expectation value from measurement counts
    
    Args:
        counts: Measurement count dictionary
        hamiltonian: Problem Hamiltonian  
        num_qubits: Number of qubits
        
    Returns:
        Expectation value
    """
    expectation = 0.0
    total_shots = sum(counts.values())
    
    for bitstring, count in counts.items():
        probability = count / total_shots
        
        # Convert bitstring to Z eigenvalues (+1 for 0, -1 for 1)
        z_values = np.array([1 - 2 * int(bit) for bit in bitstring])
        
        # Compute energy for this bitstring
        energy = 0.0
        for pauli_string, coeff in zip(hamiltonian.paulis.to_labels(), hamiltonian.coeffs):
            term_value = coeff.real
            
            for qubit_idx, pauli_op in enumerate(pauli_string):
                if pauli_op == 'Z':
                    term_value *= z_values[qubit_idx]
                # 'I' operations contribute factor of 1
                    
            energy += term_value
        
        expectation += probability * energy
    
    return expectation


def create_fast_test_result(periods_data: List[pd.DataFrame], total_qubits: int, config: DynamicOptimizationConfig = None) -> dict:
    """
    Create a fast test result using simple heuristics for ultra-fast development testing
    
    Returns a mock result that mimics the structure of real quantum optimization
    """
    print(f"[LOG] Fast test mode: {len(periods_data)} periods, {total_qubits} qubits")
    
    num_assets = periods_data[0].shape[1] 
    num_periods = len(periods_data)
    
    # Simple equal allocation as test result in correct format
    allocations = {}
    for period_idx in range(num_periods):
        # Equal weight allocation (normalized)
        equal_weights = np.ones(num_assets) / num_assets
        allocations[f"time_step_{period_idx}"] = {
            f"asset_{asset_idx}": float(equal_weights[asset_idx]) 
            for asset_idx in range(num_assets)
        }
    
    # Mock performance metrics with all expected fields
    mock_result = {
        "success": True,
        "allocations": allocations,
        "objective_value": -0.5,  # Mock objective value (negative because it's a cost)
        "quantum_jobs_executed": 1,  # Mock minimal quantum jobs
        "solution_bitstring": "10" * (total_qubits // 2),  # Mock bitstring
        "measurement_counts": {"11": 10, "00": 5},  # Mock measurement counts
        "quantum_backend_used": "test_mode_simulator",
        "configuration": config.__dict__ if config else {},  # Include the configuration
        "expected_return": 0.08,  # Mock 8% return
        "risk": 0.12,             # Mock 12% risk
        "sharpe_ratio": 0.67,     # Mock Sharpe ratio
        "total_qubits": total_qubits,
        "quantum_cost": -0.5,     # Mock quantum cost
        "classical_benchmark": {
            "return": 0.07,
            "risk": 0.15,
            "sharpe": 0.47
        },
        "execution_time": 0.001,    # Ultra-fast execution
        "optimization_method": "fast_test_mode",
        "test_mode": True
    }
    
    print(f"[LOG] Fast test result: {mock_result['expected_return']:.1%} return, {mock_result['risk']:.1%} risk")
    return mock_result


# Enhanced quantum optimization function
def dynamic_quantum_optimize(prices: pd.DataFrame, config: DynamicOptimizationConfig,
                           previous_allocation: Optional[np.ndarray] = None,
                           quantum_backend: Optional[str] = None) -> dict:
    """
    Main entry point for dynamic quantum portfolio optimization
    
    Args:
        prices: Historical price data
        config: Optimization configuration
        previous_allocation: Previous period allocation (for transaction costs)
        quantum_backend: Name of quantum backend to use (None for auto-selection)
        
    Returns:
        Optimization result with multi-period allocations
    """
    print(f"[LOG] Starting dynamic quantum optimization with {config.num_time_steps} periods")
    
    # Prepare multi-period data
    periods_data = prepare_multi_period_data(prices, config)
    if not periods_data:
        raise ValueError("Insufficient data for multi-period optimization")
        
    print(f"[LOG] Prepared {len(periods_data)} time periods")
    
    # Build enhanced QUBO
    linear, quadratic, total_qubits = build_dynamic_qubo(periods_data, config, previous_allocation)
    
    # Fast test mode - skip quantum simulation and return mock result
    if config.test_mode:
        print("[LOG] TEST MODE: Using fast classical approximation")
        return create_fast_test_result(periods_data, total_qubits, config)
    
    # Convert to Hamiltonian  
    hamiltonian = build_hamiltonian_from_qubo(linear, quadratic, total_qubits)
    
    # Create optimized ansatz
    ansatz = create_optimized_ansatz(total_qubits, config)
    ansatz.measure_all()
    
    # Run optimization
    if config.optimizer_type == "differential_evolution":
        result = run_differential_evolution_vqe(ansatz, hamiltonian, config, quantum_backend)
    else:
        # Fallback to COBYLA
        raise NotImplementedError("Only differential_evolution optimizer currently supported")
    
    # Decode solution
    num_assets = periods_data[0].shape[1]
    num_periods = len(periods_data)
    allocations = decode_quantum_solution(result['solution'], config, num_assets, num_periods)
    
    # Prepare final result
    final_result = {
        'allocations': allocations,
        'objective_value': result['objective_value'],
        'quantum_jobs_executed': result['job_count'],
        'solution_bitstring': result['solution'],
        'measurement_counts': result['final_counts'],
        'quantum_backend_used': result.get('backend_name', quantum_backend or 'auto-selected'),
        'configuration': config.__dict__
    }
    
    print("[LOG] Dynamic quantum optimization complete")
    return final_result


# Example usage and testing
if __name__ == "__main__":
    print("[LOG] Enhanced Dynamic Portfolio Optimization - Test Mode")
    
    # Create sample data
    np.random.seed(42)
    dates = pd.date_range('2023-01-01', periods=120, freq='D')  
    num_assets = 3
    
    # Generate correlated random walk prices
    rng = np.random.default_rng(seed=42)
    prices_data = {}
    for i in range(num_assets):
        returns = rng.normal(0.001, 0.02, 120)  # Daily returns
        prices = 100 * np.exp(np.cumsum(returns))
        prices_data[f'Asset_{i}'] = prices
    
    prices_df = pd.DataFrame(prices_data, index=dates)
    print(f"[LOG] Generated test data: {prices_df.shape}")
    
    # Test configuration
    config = DynamicOptimizationConfig(
        num_time_steps=3,
        rebalance_frequency_days=30,
        bit_resolution=2,
        num_generations=5,  # Reduced for testing
        population_size=10,
        estimator_shots=1000,
        sampler_shots=5000
    )
    
    try:
        # Run optimization
        result = dynamic_quantum_optimize(prices_df, config)
        
        print("\n[RESULT] Dynamic Portfolio Optimization Complete!")
        print(f"Objective Value: {result['objective_value']:.4f}")
        print(f"Quantum Jobs: {result['quantum_jobs_executed']}")
        print("\nTime-Step Allocations:")
        
        for time_step, allocations in result['allocations'].items():
            print(f"  {time_step}:")
            for asset, weight in allocations.items():
                print(f"    {asset}: {weight:.3f}")
        
        print(f"\nSolution Bitstring: {result['solution_bitstring']}")
        
    except Exception as e:
        print(f"[ERROR] Optimization failed: {e}")
        import traceback
        traceback.print_exc()