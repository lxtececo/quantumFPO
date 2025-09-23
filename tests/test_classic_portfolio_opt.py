import json
import pytest
from backend.src.main.python.classic_portfolio_opt import optimize_portfolio

def test_optimize_portfolio_basic():
    stock_data = [
        {"symbol": "AAPL", "date": "2025-09-01", "close": 150.0},
        {"symbol": "AAPL", "date": "2025-09-02", "close": 152.0},
        {"symbol": "AAPL", "date": "2025-09-03", "close": 151.0}
    ]
    result = optimize_portfolio(stock_data, 5)
    assert "weights" in result
    assert "expected_annual_return" in result
    assert "annual_volatility" in result
    assert "sharpe_ratio" in result
    assert "value_at_risk" in result
