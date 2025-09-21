import sys
import json
import numpy as np
import pandas as pd
from pypfopt import EfficientFrontier, expected_returns
from pypfopt.risk_models import CovarianceShrinkage

def optimize_portfolio(stock_data, var_percent):
    # stock_data: list of dicts {symbol, date, open, high, low, close}
    df = pd.DataFrame(stock_data)
    # Use close prices for optimization, but open/high/low are available for extension
    prices = df.pivot(index='date', columns='symbol', values='close').sort_index()
    # Optionally, you could use open/high/low for other analytics or constraints
    mu = expected_returns.mean_historical_return(prices)
    S = CovarianceShrinkage(prices).ledoit_wolf()
    ef = EfficientFrontier(mu, S)
    ef.max_sharpe()
    cleaned_weights = ef.clean_weights()
    perf = ef.portfolio_performance(verbose=False)
    result = {
        'weights': cleaned_weights,
        'expected_annual_return': perf[0],
        'annual_volatility': perf[1],
        'sharpe_ratio': perf[2],
        'value_at_risk': var_percent
    }
    return result

if __name__ == '__main__':
    try:
        input_data = json.load(sys.stdin)
        stock_data = input_data['stock_data']
        var_percent = input_data['var_percent']
        result = optimize_portfolio(stock_data, var_percent)
        print(json.dumps(result))
    except Exception as e:
        print(json.dumps({'error': str(e)}))
