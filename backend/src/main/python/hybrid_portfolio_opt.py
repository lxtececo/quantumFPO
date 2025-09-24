import sys
import json
import numpy as np
import pandas as pd
from pypfopt import EfficientFrontier, expected_returns
from pypfopt.risk_models import CovarianceShrinkage
from qiskit.quantum_info import SparsePauliOp
from qiskit.circuit.library import QAOAAnsatz
from qiskit.transpiler import generate_preset_pass_manager

from qiskit_aer import AerSimulator
from scipy.optimize import minimize

def classical_optimize(prices):
    print("[LOG] [Classic] Step 1: Starting classical optimization")
    mu = expected_returns.mean_historical_return(prices)
    print(f"[LOG] [Classic] Step 2: Calculated expected returns: {mu}")
    S = CovarianceShrinkage(prices).ledoit_wolf()
    print(f"[LOG] [Classic] Step 3: Calculated covariance matrix: {S}")
    ef = EfficientFrontier(mu, S)
    print("[LOG] [Classic] Step 4: Created EfficientFrontier object")
    ef.max_sharpe()
    print("[LOG] [Classic] Step 5: Maximized Sharpe ratio")
    weights = ef.clean_weights()
    print(f"[LOG] [Classic] Step 6: Cleaned weights: {weights}")
    perf = ef.portfolio_performance(verbose=False)
    print(f"[LOG] [Classic] Step 7: Portfolio performance: {perf}")
    print("[LOG] [Classic] Step 8: Classical optimization complete")
    return weights, perf

# Quantum optimization using Qiskit Optimization API (QUBO + VQE)
def build_qubo(prices, risk_aversion):
    num_assets = prices.shape[1]
    mu = expected_returns.mean_historical_return(prices)
    S = CovarianceShrinkage(prices).ledoit_wolf()
    linear = np.array([-mu.iloc[i] for i in range(num_assets)])
    quadratic = np.zeros((num_assets, num_assets))
    for i in range(num_assets):
        quadratic[i, i] = risk_aversion * S.iloc[i, i]
        for j in range(i+1, num_assets):
            quadratic[i, j] = risk_aversion * S.iloc[i, j]
            quadratic[j, i] = risk_aversion * S.iloc[i, j]
    return linear, quadratic, num_assets

def build_hamiltonian(linear, quadratic, num_assets):
    pauli_terms = []
    for i in range(num_assets):
        coeff = linear[i]
        label = 'I' * i + 'Z' + 'I' * (num_assets - i - 1)
        pauli_terms.append((label, coeff))
    for i in range(num_assets):
        for j in range(i+1, num_assets):
            coeff = quadratic[i, j]
            label = ['I'] * num_assets
            label[i] = 'Z'
            label[j] = 'Z'
            pauli_terms.append((''.join(label), coeff))
    return SparsePauliOp.from_list(pauli_terms)

def run_simulator(ansatz, hamiltonian, num_assets, init_params):
    from qiskit_aer import AerSimulator
    from qiskit_ibm_runtime import SamplerV2 as Sampler
    aer = AerSimulator()
    pm = generate_preset_pass_manager(backend=aer, optimization_level=1)
    def bitstring_to_z(bitstr, n):
        bits = np.array([int(b) for b in format(bitstr, f'0{n}b')])
        return 1 - 2 * bits
    def compute_expectation(counts, hamiltonian, n):
        exp = 0.0
        shots = sum(counts.values())
        for bitstr, prob in counts.items():
            z = bitstring_to_z(bitstr, n)
            value = 0.0
            for label, coeff in zip(hamiltonian.paulis.to_labels(), hamiltonian.coeffs):
                term = coeff.real
                for idx, op in enumerate(label):
                    if op == 'Z':
                        term *= z[idx]
                value += term
            exp += (prob / shots) * value
        return exp
    sampler_job_count = 0
    def cost_func(params):
        nonlocal sampler_job_count
        circ = ansatz.assign_parameters(params)
        isa_circ = pm.run(circ)
        sampler = Sampler(mode=aer)
        sampler_job_count += 1
        print(f'[LOG] [Simulator] Submitting sampler job #{sampler_job_count}')
        job = sampler.run([isa_circ], shots=1024)
        print(f'[LOG] [Simulator] Sampler job id: {job.job_id()} (Job #{sampler_job_count})')
        result = job.result()
        counts = result[0].data.meas.get_int_counts()
        exp = compute_expectation(counts, hamiltonian, num_assets)
        return exp
    print('[LOG] [Simulator] Starting minimization with COByLA')
    opt_result = minimize(cost_func, init_params, method="COBYLA", options={"maxiter": 50})
    print('[LOG] [Simulator] Minimization complete, submitting final sampler job')
    final_circ = ansatz.assign_parameters(opt_result.x)
    isa_final_circ = pm.run(final_circ)
    sampler = Sampler(mode=aer)
    sampler_job_count += 1
    job = sampler.run([isa_final_circ], shots=2048)
    print(f'[LOG] [Simulator] Final sampler job id: {job.job_id()} (Job #{sampler_job_count})')
    result = job.result()
    counts = result[0].data.meas.get_int_counts()
    best_bitstr = max(counts, key=counts.get)
    solution = [int(b) for b in format(best_bitstr, f'0{num_assets}b')]
    print(f'[LOG] [Simulator] Total sampler jobs executed: {sampler_job_count}')
    return {
        'solution': solution,
        'objective_value': opt_result.fun,
        'simulator_sampler_jobs_executed': sampler_job_count
    }

def run_real_backend(ansatz, hamiltonian, num_assets, init_params):
    from qiskit_ibm_runtime import QiskitRuntimeService, EstimatorV2 as Estimator, SamplerV2 as Sampler
    import os
    print('[LOG] [RealBackend] Step 1: Initializing QiskitRuntimeService')
    # COBYLA maxiter default is 1000, but we use tol=1e-2, so actual may be less
    # We can estimate from init_params size, but let's log the minimizer options
    print(f'[LOG] [RealBackend] Minimizer options: method=COBYLA, tol=1e-2, init_params={len(init_params)}')
    service = QiskitRuntimeService()
    print('[LOG] [RealBackend] Step 2: Selecting least busy backend')
    backend = service.least_busy()
    print(f'[LOG] [RealBackend] Step 3: Selected backend: {backend}')
    print('[LOG] [RealBackend] Step 4: Generating preset pass manager')
    pm = generate_preset_pass_manager(optimization_level=3, backend=backend)
    print('[LOG] [RealBackend] Step 5: Running pass manager on ansatz')
    candidate_circuit = pm.run(ansatz)
    objective_func_vals = []
    estimator_job_count = 0
    sampler_job_count = 0
    def cost_func_estimator(params, ansatz, hamiltonian, estimator):
        nonlocal estimator_job_count
        print('[LOG] [RealBackend] Step 6: Running cost_func_estimator')
        isa_hamiltonian = hamiltonian.apply_layout(ansatz.layout)
        pub = (ansatz, isa_hamiltonian, params)
        print('[LOG] [RealBackend] Step 7: Submitting estimator job')
        job = estimator.run([pub])
        estimator_job_count += 1
        print(f'[LOG] [RealBackend] Estimator job id: {job.job_id()} (Job #{estimator_job_count})')
        import time
        while not job.done():
            status = getattr(job, 'status', lambda: None)()
            print(f'[LOG] [RealBackend] Waiting for estimator job to complete. Status: {status}, Job ID: {job.job_id()}')
            if status == 'ERROR':
                print(f'[LOG] [RealBackend] Estimator job ERROR. Job ID: {job.job_id()}')
                break
            time.sleep(5)
        if getattr(job, 'status', lambda: None)() == 'ERROR':
            print(f'[LOG] [RealBackend] Estimator job ended in ERROR state. Job ID: {job.job_id()}')
            # Do not raise, just return None to continue execution
            return None
        print('[LOG] [RealBackend] Step 9: Estimator job completed, fetching result')
        results = job.result()[0]
        cost = results.data.evs
        print(f'[LOG] [RealBackend] Step 10: Cost function value: {cost}')
        objective_func_vals.append(cost)
        return cost
    print('[LOG] [RealBackend] Step 11: Initializing Estimator in backend mode')
    estimator = Estimator(mode=backend)
    estimator.options.default_shots = 1000
    estimator.options.dynamical_decoupling.enable = True
    estimator.options.dynamical_decoupling.sequence_type = "XY4"
    estimator.options.twirling.enable_gates = True
    estimator.options.twirling.num_randomizations = "auto"
    print('[LOG] [RealBackend] Step 12: Running minimization')
    result = minimize(
        cost_func_estimator,
        init_params,
        args=(candidate_circuit, hamiltonian, estimator),
        method="COBYLA",
        tol=1e-2,
    )
    print('[LOG] [RealBackend] Step 13: Minimization complete, assigning optimized parameters')
    optimized_circuit = candidate_circuit.assign_parameters(result.x)
    print('[LOG] [RealBackend] Step 14: Initializing Sampler in backend mode')
    sampler = Sampler(mode=backend)
    sampler.options.default_shots = 10000
    sampler.options.dynamical_decoupling.enable = True
    sampler.options.dynamical_decoupling.sequence_type = "XY4"
    sampler.options.twirling.enable_gates = True
    sampler.options.twirling.num_randomizations = "auto"
    pub = (optimized_circuit,)
    print('[LOG] [RealBackend] Step 15: Submitting sampler job')
    job = sampler.run([pub], shots=int(1e4))
    sampler_job_count += 1
    print(f'[LOG] [RealBackend] Sampler job id: {job.job_id()} (Job #{sampler_job_count})')
    import time
    while not job.done():
        status = getattr(job, 'status', lambda: None)()
        print(f'[LOG] [RealBackend] Waiting for sampler job to complete. Status: {status}, Job ID: {job.job_id()}')
        if status == 'ERROR':
            print(f'[LOG] [RealBackend] Sampler job ERROR. Job ID: {job.job_id()}')
            break
        time.sleep(5)
    if getattr(job, 'status', lambda: None)() == 'ERROR':
        print(f'[LOG] [RealBackend] Sampler job ended in ERROR state. Job ID: {job.job_id()}')
        # Do not raise, just return None to continue execution
        return {
            'solution': None,
            'objective_value': None
        }
    print('[LOG] [RealBackend] Step 17: Sampler job completed, fetching result')
    counts_int = job.result()[0].data.meas.get_int_counts()
    shots = sum(counts_int.values())
    final_distribution_int = {key: val / shots for key, val in counts_int.items()}
    most_likely = max(final_distribution_int, key=final_distribution_int.get)
    solution = [int(b) for b in format(most_likely, f'0{num_assets}b')]
    print(f'[LOG] [RealBackend] Step 18: Solution bitstring: {solution}')
    print(f'[LOG] [RealBackend] Step 19: Objective value: {result.fun}')
    print(f'[LOG] [RealBackend] Summary: Estimator jobs executed: {estimator_job_count}, Sampler jobs executed: {sampler_job_count}')
    return {
        'solution': solution,
        'objective_value': result.fun,
        'estimator_jobs_executed': estimator_job_count,
        'sampler_jobs_executed': sampler_job_count
    }

def quantum_optimize(prices, risk_aversion=0.5):
    print("[LOG] Starting quantum optimization", file=sys.stderr)
    linear, quadratic, num_assets = build_qubo(prices, risk_aversion)
    print(f"[LOG] Quantum: Number of assets = {num_assets}", file=sys.stderr)
    print("[LOG] Quantum: Built QUBO coefficients", file=sys.stderr)
    hamiltonian = build_hamiltonian(linear, quadratic, num_assets)
    print("[LOG] Quantum: Built cost Hamiltonian", file=sys.stderr)
    reps = 2
    ansatz = QAOAAnsatz(cost_operator=hamiltonian, reps=reps)
    ansatz.measure_all()
    print("[LOG] Quantum: Built QAOA ansatz circuit", file=sys.stderr)
    rng = np.random.default_rng(42)
    init_params = rng.uniform(0, 2 * np.pi, ansatz.num_parameters)
    if qc_simulator_mode:
        print("[LOG] Using AerSimulator backend", file=sys.stderr)
        return run_simulator(ansatz, hamiltonian, num_assets, init_params)
    else:
        print("[LOG] Using IBM Quantum backend", file=sys.stderr)
        return run_real_backend(ansatz, hamiltonian, num_assets, init_params)

import os

if __name__ == '__main__':
    try:
        # Read input from a JSON file (path passed as first argument)
        # Second argument: 'simulator' or 'real'
        if len(sys.argv) < 3:
            print(json.dumps({'error': 'Missing input file path or backend mode'}), file=sys.stdout)
            sys.exit(1)
        input_path = sys.argv[1]
        qc_mode = sys.argv[2].lower() if len(sys.argv) > 2 else 'simulator'
        global qc_simulator_mode
        qc_simulator_mode = (qc_mode == 'simulator')
        if not os.path.exists(input_path):
            print(json.dumps({'error': f'Input file not found: {input_path}'}), file=sys.stdout)
            sys.exit(2)
        with open(input_path, 'r', encoding='utf-8') as f:
            raw_input = f.read()
        print(f"[PYTHON] Received raw input from file {input_path}: {raw_input}", file=sys.stderr)
        try:
            input_data = json.loads(raw_input)
        except Exception as parse_ex:
            print(json.dumps({'error': f'JSON parse error: {str(parse_ex)}', 'raw_input': raw_input}), file=sys.stdout)
            sys.exit(3)
        stock_data = input_data.get('stock_data', None)
        var_percent = input_data.get('var_percent', None)
        if stock_data is None:
            print(json.dumps({'error': 'Missing stock_data in input', 'input': input_data}), file=sys.stdout)
            sys.exit(4)
        # Only 'close' is used; no need to pop other columns
        df = pd.DataFrame(stock_data)
        prices = df.pivot(index='date', columns='symbol', values='close').sort_index()
        print("[LOG] Running classical optimizer...", file=sys.stderr)
        weights, perf = classical_optimize(prices)
        print("[LOG] Running quantum optimizer...", file=sys.stderr)
        quantum_result = quantum_optimize(prices)
        print("[LOG] Both optimizations complete.", file=sys.stderr)
        result = {
            'classical_weights': weights,
            'classical_performance': {
                'expected_annual_return': perf[0],
                'annual_volatility': perf[1],
                'sharpe_ratio': perf[2]
            },
            'quantum_qaoa_result': quantum_result,
            'value_at_risk': var_percent
        }
        print(json.dumps(result), file=sys.stdout)
    except Exception as e:
        print(json.dumps({'error': str(e)}), file=sys.stdout)
        sys.exit(5)
