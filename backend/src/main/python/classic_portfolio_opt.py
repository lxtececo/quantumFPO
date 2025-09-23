import sys
import json
import numpy as np
import pandas as pd
from pypfopt import EfficientFrontier, expected_returns
from pypfopt.risk_models import CovarianceShrinkage

def optimize_portfolio(stock_data, var_percent):
    print('[LOG] [Classic] Step 1: Received stock data for optimization')
    df = pd.DataFrame(stock_data)
    print(f'[LOG] [Classic] Step 2: Created DataFrame with shape {df.shape}')
    prices = df.pivot(index='date', columns='symbol', values='close').sort_index()
    print(f'[LOG] [Classic] Step 3: Pivoted prices DataFrame with shape {prices.shape}')
    mu = expected_returns.mean_historical_return(prices)
    print(f'[LOG] [Classic] Step 4: Calculated expected returns: {mu}')
    S = CovarianceShrinkage(prices).ledoit_wolf()
    print('[LOG] [Classic] Step 5: Calculated covariance matrix')
    ef = EfficientFrontier(mu, S)
    print('[LOG] [Classic] Step 6: Created EfficientFrontier object')
    ef.max_sharpe()
    print('[LOG] [Classic] Step 7: Maximized Sharpe ratio')
    cleaned_weights = ef.clean_weights()
    print(f'[LOG] [Classic] Step 8: Cleaned weights: {cleaned_weights}')
    perf = ef.portfolio_performance(verbose=False)
    print(f'[LOG] [Classic] Step 9: Portfolio performance: {perf}')
    print('[LOG] [Classic] Step 10: Classical optimization complete')
    result = {
        'weights': cleaned_weights,
        'expected_annual_return': perf[0],
        'annual_volatility': perf[1],
        'sharpe_ratio': perf[2],
        'value_at_risk': var_percent
    }
    return result

if __name__ == '__main__':
    import sys
    import os
    try:
        if len(sys.argv) != 3:
            print(json.dumps({'error': 'Usage: classic_portfolio_opt.py <input_json_path> <output_json_path>'}))
            sys.exit(1)
        input_json_path = sys.argv[1]
        output_json_path = sys.argv[2]
        with open(input_json_path, 'r') as f:
            input_data = json.load(f)
        stock_data = input_data['stock_data']
        var_percent = input_data['var_percent']
        result = optimize_portfolio(stock_data, var_percent)
        with open(output_json_path, 'w') as f:
            json.dump(result, f)
    except Exception as e:
        # Write error to output file
        if 'output_json_path' in locals():
            with open(output_json_path, 'w') as f:
                json.dump({'error': str(e)}, f)
        else:
            print(json.dumps({'error': str(e)}))
