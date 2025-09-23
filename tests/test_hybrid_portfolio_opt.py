import pytest
from backend.src.main.python.hybrid_portfolio_opt import build_qubo, build_hamiltonian

def test_build_qubo_and_hamiltonian():
    import pandas as pd
    prices = pd.DataFrame({
        'AAPL': [150, 152, 151],
        'GOOG': [2800, 2820, 2810]
    }, index=['2025-09-01', '2025-09-02', '2025-09-03'])
    linear, quadratic, num_assets = build_qubo(prices, 0.5)
    hamiltonian = build_hamiltonian(linear, quadratic, num_assets)
    assert len(linear) == num_assets
    assert quadratic.shape == (num_assets, num_assets)
    assert hasattr(hamiltonian, 'paulis')
