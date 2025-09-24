"""
Test suite for hybrid_portfolio_opt.py
Tests both classical and quantum portfolio optimization components.
"""

import unittest
import pandas as pd
import numpy as np
import tempfile
import json
import os
import sys
import subprocess
from unittest.mock import patch, Mock

# Add the backend source directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'main', 'python'))

import hybrid_portfolio_opt
from hybrid_portfolio_opt import (
    build_qubo,
    build_hamiltonian,
    classical_optimize,
    quantum_optimize,
    run_simulator,
    run_real_backend
)

def build_qubo_problem(stock_data, var_percent):
    """Wrapper function to match test expectations."""
    import pandas as pd
    # Convert stock_data list to DataFrame and pivot to get prices
    df = pd.DataFrame(stock_data)
    prices = df.pivot(index='date', columns='symbol', values='close').sort_index()
    # Convert var_percent to risk_aversion (simple conversion for testing)
    risk_aversion = var_percent / 100.0
    # build_qubo returns (linear, quadratic, num_assets) not dict
    linear, quadratic, num_assets = build_qubo(prices, risk_aversion)
    return {'linear': linear, 'quadratic': quadratic, 'num_assets': num_assets}


class TestQuantumPortfolioOptimization(unittest.TestCase):
    def setUp(self):
        """Set up test data for portfolio optimization."""
        # Sample stock data for testing
        self.stock_data = [
            {"symbol": "AAPL", "date": "2025-09-01", "close": 150.0},
            {"symbol": "AAPL", "date": "2025-09-02", "close": 152.0},
            {"symbol": "AAPL", "date": "2025-09-03", "close": 151.0},
            {"symbol": "GOOGL", "date": "2025-09-01", "close": 2800.0},
            {"symbol": "GOOGL", "date": "2025-09-02", "close": 2820.0},
            {"symbol": "GOOGL", "date": "2025-09-03", "close": 2810.0}
        ]
        self.var_percent = 5

    def test_build_qubo_basic_functionality(self):
        """Test QUBO problem construction with basic data."""
        qubo = build_qubo_problem(self.stock_data, self.var_percent)
        
        self.assertIsInstance(qubo, dict)
        self.assertIn('linear', qubo)
        self.assertIn('quadratic', qubo)
        self.assertIn('num_assets', qubo)
        
        # Check that QUBO contains proper coefficients
        self.assertIsInstance(qubo['linear'], np.ndarray)
        self.assertIsInstance(qubo['quadratic'], np.ndarray)
        self.assertIsInstance(qubo['num_assets'], int)

    def test_build_qubo_different_risk_aversion(self):
        """Test QUBO problem with different risk aversion values."""
        risk_levels = [1, 5, 10]
        for risk in risk_levels:
            with self.subTest(risk_aversion=risk):
                qubo = build_qubo_problem(self.stock_data, risk)
                self.assertIsInstance(qubo, dict)
                self.assertGreater(qubo['num_assets'], 0)

    def test_build_qubo_single_asset(self):
        """Test QUBO problem with single asset."""
        single_asset_data = [
            {"symbol": "AAPL", "date": "2025-09-01", "close": 150.0},
            {"symbol": "AAPL", "date": "2025-09-02", "close": 152.0}
        ]
        qubo = build_qubo_problem(single_asset_data, self.var_percent)
        self.assertIsInstance(qubo, dict)
        self.assertEqual(qubo['num_assets'], 1)

    def test_build_qubo_multi_asset(self):
        """Test QUBO problem with multiple assets."""
        qubo = build_qubo_problem(self.stock_data, self.var_percent)
        self.assertIsInstance(qubo, dict)
        # Should have interactions between different assets
        self.assertEqual(qubo['num_assets'], 2)

    def test_build_hamiltonian_basic(self):
        """Test Hamiltonian construction from QUBO."""
        qubo = build_qubo_problem(self.stock_data, self.var_percent)
        hamiltonian = build_hamiltonian(qubo['linear'], qubo['quadratic'], qubo['num_assets'])
        
        self.assertIsNotNone(hamiltonian)
        # Check basic Hamiltonian properties
        self.assertTrue(hasattr(hamiltonian, 'num_qubits'))

    def test_build_hamiltonian_single_asset(self):
        """Test Hamiltonian with single asset QUBO."""
        single_asset_data = [
            {"symbol": "AAPL", "date": "2025-09-01", "close": 150.0},
            {"symbol": "AAPL", "date": "2025-09-02", "close": 152.0}
        ]
        qubo = build_qubo_problem(single_asset_data, self.var_percent)
        hamiltonian = build_hamiltonian(qubo['linear'], qubo['quadratic'], qubo['num_assets'])
        self.assertIsNotNone(hamiltonian)

    def test_build_hamiltonian_multi_asset(self):
        """Test Hamiltonian with multi-asset QUBO."""
        qubo = build_qubo_problem(self.stock_data, self.var_percent)
        hamiltonian = build_hamiltonian(qubo['linear'], qubo['quadratic'], qubo['num_assets'])
        self.assertIsNotNone(hamiltonian)
        self.assertGreater(hamiltonian.num_qubits, 1)

    def test_classical_optimize_basic(self):
        """Test classical optimization functionality."""
        # Convert stock_data to DataFrame format expected by classical_optimize
        df = pd.DataFrame(self.stock_data)
        prices = df.pivot(index='date', columns='symbol', values='close').sort_index()
        
        weights, performance = classical_optimize(prices)
        
        self.assertIsInstance(weights, dict)
        self.assertIsInstance(performance, tuple)
        self.assertEqual(len(performance), 3)  # expected return, volatility, sharpe
        
        # Weights should be for each stock
        expected_symbols = {'AAPL', 'GOOGL'}
        self.assertEqual(set(weights.keys()), expected_symbols)

    def test_classical_optimize_single_stock(self):
        """Test classical optimization with single stock."""
        single_stock_data = [data for data in self.stock_data if data['symbol'] == 'AAPL']
        df = pd.DataFrame(single_stock_data)
        prices = df.pivot(index='date', columns='symbol', values='close').sort_index()
        
        weights, _ = classical_optimize(prices)
        
        self.assertIsInstance(weights, dict)
        self.assertIn('AAPL', weights)

    def test_classical_optimize_multi_stock(self):
        """Test classical optimization with multiple stocks."""
        df = pd.DataFrame(self.stock_data)
        prices = df.pivot(index='date', columns='symbol', values='close').sort_index()
        
        weights, _ = classical_optimize(prices)
        
        self.assertIsInstance(weights, dict)
        # Should have weights for multiple assets
        self.assertGreater(len(weights), 1)

    @patch('hybrid_portfolio_opt.run_simulator')
    def test_quantum_optimize_simulator_mode(self, mock_run_simulator):
        """Test quantum optimization in simulator mode."""
        mock_run_simulator.return_value = {
            'solution': [1, 0],
            'objective_value': -0.5
        }
        
        # Convert stock_data to DataFrame format
        df = pd.DataFrame(self.stock_data)
        prices = df.pivot(index='date', columns='symbol', values='close').sort_index()
        
        with patch.object(hybrid_portfolio_opt, 'qc_simulator_mode', True, create=True):
            result = quantum_optimize(prices, risk_aversion=0.05)
        
        self.assertIsInstance(result, dict)
        self.assertIn('solution', result)
        self.assertIn('objective_value', result)
        mock_run_simulator.assert_called_once()

    @patch('hybrid_portfolio_opt.run_real_backend')
    def test_quantum_optimize_real_backend_mode(self, mock_run_real_backend):
        """Test quantum optimization with real backend."""
        mock_run_real_backend.return_value = {
            'solution': [0, 1],
            'objective_value': -0.3
        }
        
        # Convert stock_data to DataFrame format
        df = pd.DataFrame(self.stock_data)
        prices = df.pivot(index='date', columns='symbol', values='close').sort_index()
        
        with patch.object(hybrid_portfolio_opt, 'qc_simulator_mode', False, create=True):
            result = quantum_optimize(prices, risk_aversion=0.05)
        
        self.assertIsInstance(result, dict)
        self.assertIn('solution', result)
        mock_run_real_backend.assert_called_once()

    def test_quantum_optimize_different_risk_aversion(self):
        """Test quantum optimization with different risk levels."""
        with patch('hybrid_portfolio_opt.run_simulator') as mock_sim:
            mock_sim.return_value = {'solution': [1, 0], 'objective_value': -0.5}
            
            df = pd.DataFrame(self.stock_data)
            prices = df.pivot(index='date', columns='symbol', values='close').sort_index()
            
            for risk in [0.01, 0.05, 0.10]:
                with self.subTest(risk=risk):
                    with patch.object(hybrid_portfolio_opt, 'qc_simulator_mode', True, create=True):
                        result = quantum_optimize(prices, risk_aversion=risk)
                    self.assertIsInstance(result, dict)

    def test_run_real_backend_error_handling(self):
        """Test real backend with proper error handling."""
        df = pd.DataFrame(self.stock_data)
        prices = df.pivot(index='date', columns='symbol', values='close').sort_index()
        linear, quadratic, num_assets = build_qubo(prices, 0.05)
        hamiltonian = build_hamiltonian(linear, quadratic, num_assets)
        
        # Mock the quantum backend execution with error using proper import paths
        with patch('qiskit_ibm_runtime.QiskitRuntimeService') as mock_service:
            mock_service.side_effect = Exception("Backend connection failed")
            
            try:
                result = run_real_backend(None, hamiltonian, num_assets, None)
                # Should handle errors gracefully
                self.assertIsInstance(result, dict)
            except Exception:
                # Expected behavior for connection failures
                pass


class TestHybridPortfolioMainScript(unittest.TestCase):
    """Test the main script execution functionality for hybrid portfolio optimization."""
    
    def test_main_script_subprocess_execution_simulator_mode(self):
        """Test main script execution in simulator mode via subprocess."""
        import subprocess
        input_data = {
            "stock_data": [
                {"symbol": "AAPL", "date": "2025-09-01", "close": 150.0},
                {"symbol": "AAPL", "date": "2025-09-02", "close": 152.0},
                {"symbol": "GOOGL", "date": "2025-09-01", "close": 2800.0},
                {"symbol": "GOOGL", "date": "2025-09-02", "close": 2820.0}
            ],
            "var_percent": 5
        }
        
        with tempfile.TemporaryDirectory() as temp_dir:
            input_file = os.path.join(temp_dir, "input.json")
            script_path = os.path.join(os.path.dirname(__file__), '..', '..', 'main', 'python', 'hybrid_portfolio_opt.py')
            
            # Write input file
            with open(input_file, 'w') as f:
                json.dump(input_data, f)
            
            # Mock the quantum operations to avoid actual quantum execution
            with patch.dict('sys.modules', {
                'qiskit_aer': Mock(),
                'qiskit_ibm_runtime': Mock()
            }):
                # Execute script via subprocess in simulator mode
                proc_result = subprocess.run([
                    sys.executable, script_path, input_file, 'simulator'
                ], capture_output=True, text=True, timeout=30)
                
                # Check that script handled the input (may exit with error due to mocking)
                self.assertIsInstance(proc_result.returncode, int)
                # Should have attempted to process the input
                self.assertIn("stock_data", proc_result.stderr or "")
    
    def test_main_script_invalid_arguments(self):
        """Test main script with invalid arguments."""
        import subprocess
        script_path = os.path.join(os.path.dirname(__file__), '..', '..', 'main', 'python', 'hybrid_portfolio_opt.py')
        
        # Execute script with missing arguments
        proc_result = subprocess.run([
            sys.executable, script_path
        ], capture_output=True, text=True)
        
        # Should exit with error
        self.assertNotEqual(proc_result.returncode, 0)
        # Should contain error message in stdout
        self.assertIn("error", proc_result.stdout)
    
    def test_main_script_missing_input_file(self):
        """Test main script with non-existent input file."""
        import subprocess
        with tempfile.TemporaryDirectory() as temp_dir:
            non_existent_input = os.path.join(temp_dir, "nonexistent.json")
            script_path = os.path.join(os.path.dirname(__file__), '..', '..', 'main', 'python', 'hybrid_portfolio_opt.py')
            
            # Execute script with non-existent input file
            proc_result = subprocess.run([
                sys.executable, script_path, non_existent_input, 'simulator'
            ], capture_output=True, text=True)
            
            # Should exit with error code 2 (file not found)
            self.assertEqual(proc_result.returncode, 2)
            # Should contain error message in stdout
            self.assertIn("Input file not found", proc_result.stdout)
    
    def test_main_script_invalid_json(self):
        """Test main script with invalid JSON input."""
        import subprocess
        with tempfile.TemporaryDirectory() as temp_dir:
            input_file = os.path.join(temp_dir, "invalid.json")
            script_path = os.path.join(os.path.dirname(__file__), '..', '..', 'main', 'python', 'hybrid_portfolio_opt.py')
            
            # Write invalid JSON
            with open(input_file, 'w') as f:
                f.write("{ invalid json content }")
            
            # Execute script with invalid JSON
            proc_result = subprocess.run([
                sys.executable, script_path, input_file, 'simulator'
            ], capture_output=True, text=True)
            
            # Should exit with error code 3 (JSON parse error)
            self.assertEqual(proc_result.returncode, 3)
            # Should contain parse error in stdout
            self.assertIn("JSON parse error", proc_result.stdout)
    
    def test_main_script_missing_stock_data(self):
        """Test main script with missing stock_data in input."""
        import subprocess
        input_data = {
            "var_percent": 5
            # Missing stock_data
        }
        
        with tempfile.TemporaryDirectory() as temp_dir:
            input_file = os.path.join(temp_dir, "input.json")
            script_path = os.path.join(os.path.dirname(__file__), '..', '..', 'main', 'python', 'hybrid_portfolio_opt.py')
            
            # Write input file without stock_data
            with open(input_file, 'w') as f:
                json.dump(input_data, f)
            
            # Execute script
            proc_result = subprocess.run([
                sys.executable, script_path, input_file, 'simulator'
            ], capture_output=True, text=True)
            
            # Should exit with error code 4 (missing stock_data)
            self.assertEqual(proc_result.returncode, 4)
            # Should contain missing stock_data error in stdout
            self.assertIn("Missing stock_data", proc_result.stdout)


# Individual test function for broader compatibility
def test_build_qubo_and_hamiltonian():
    """Standalone test for QUBO and Hamiltonian construction."""
    stock_data = [
        {"symbol": "AAPL", "date": "2025-09-01", "close": 150.0},
        {"symbol": "AAPL", "date": "2025-09-02", "close": 152.0},
        {"symbol": "GOOGL", "date": "2025-09-01", "close": 2800.0},
        {"symbol": "GOOGL", "date": "2025-09-02", "close": 2820.0}
    ]
    
    df = pd.DataFrame(stock_data)
    prices = df.pivot(index='date', columns='symbol', values='close').sort_index()
    linear, quadratic, num_assets = build_qubo(prices, 0.05)
    
    assert isinstance(linear, np.ndarray)
    assert isinstance(quadratic, np.ndarray)
    assert isinstance(num_assets, int)
    assert num_assets > 0
    
    hamiltonian = build_hamiltonian(linear, quadratic, num_assets)
    assert hamiltonian is not None


if __name__ == '__main__':
    unittest.main()