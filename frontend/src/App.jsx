import React, { useState, useEffect } from 'react';
import './App.css';
import { Line } from 'react-chartjs-2';
import { LoadingProvider, useLoading } from './context/LoadingContext';
import BlochSpinner from './components/BlochSpinner';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend
} from 'chart.js';

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, Title, Tooltip, Legend);

// Result formatter to create unified display format
const formatOptimizationResult = (result, type) => {
  if (result.error) {
    return { error: result.error };
  }

  const formatted = {
    type: type,
    success: true
  };

  switch (type) {
    case 'classic':
      formatted.weights = result.weights;
      formatted.performance = {
        'Expected Annual Return': `${(result.expected_annual_return * 100).toFixed(2)}%`,
        'Annual Volatility': `${(result.annual_volatility * 100).toFixed(2)}%`,
        'Sharpe Ratio': result.sharpe_ratio.toFixed(3),
        'Value at Risk': `${(result.value_at_risk * 100).toFixed(1)}%`
      };
      break;
      
    case 'hybrid':
      formatted.classical_weights = result.classical_weights;
      formatted.performance = {
        'Expected Annual Return': `${(result.classical_performance.expected_annual_return * 100).toFixed(2)}%`,
        'Annual Volatility': `${(result.classical_performance.annual_volatility * 100).toFixed(2)}%`,
        'Sharpe Ratio': result.classical_performance.sharpe_ratio.toFixed(3),
        'Value at Risk': `${(result.value_at_risk * 100).toFixed(1)}%`
      };
      formatted.quantum_result = {
        'Solution': result.quantum_qaoa_result.solution?.join(', ') || 'N/A',
        'Objective Value': result.quantum_qaoa_result.objective_value?.toFixed(4) || 'N/A',
        'Quantum Jobs': result.quantum_qaoa_result.simulator_sampler_jobs_executed || 'N/A'
      };
      break;
      
    case 'dynamic':
      if (result.allocations) {
        formatted.allocations = result.allocations;
      }
      formatted.performance = {
        'Objective Value': result.objective_value?.toFixed(4) || 'N/A',
        'Quantum Jobs': result.quantum_jobs_count || 'N/A',
        'Status': result.status || 'completed'
      };
      break;
      
    default:
      formatted.raw_data = result;
  }

  return formatted;
};

// Component to render formatted results
const OptimizationResultDisplay = ({ result, type, title }) => {
  if (!result) return null;

  const formatted = formatOptimizationResult(result, type);

  if (formatted.error) {
    return (
      <div>
        <h3>{title}</h3>
        <p className="error">{formatted.error}</p>
      </div>
    );
  }

  return (
    <div>
      <h3>{title}</h3>
      
      {/* Weights/Allocations Section */}
      {formatted.weights && (
        <div className="result-section">
          <h4>Portfolio Weights</h4>
          <div className="weights-grid">
            {Object.entries(formatted.weights).map(([asset, weight]) => (
              <div key={asset} className="weight-item">
                <span className="asset-name">{asset}:</span>
                <span className="weight-value">{(weight * 100).toFixed(2)}%</span>
              </div>
            ))}
          </div>
        </div>
      )}
      
      {formatted.classical_weights && (
        <div className="result-section">
          <h4>Classical Portfolio Weights</h4>
          <div className="weights-grid">
            {Object.entries(formatted.classical_weights).map(([asset, weight]) => (
              <div key={asset} className="weight-item">
                <span className="asset-name">{asset}:</span>
                <span className="weight-value">{(weight * 100).toFixed(2)}%</span>
              </div>
            ))}
          </div>
        </div>
      )}
      
      {formatted.allocations && (
        <div className="result-section">
          <h4>Multi-Period Allocations</h4>
          {Object.entries(formatted.allocations).map(([period, allocation]) => (
            <div key={period} className="period-allocation">
              <h5>{period.replace('_', ' ')}</h5>
              <div className="weights-grid">
                {Object.entries(allocation).map(([asset, weight]) => (
                  <div key={asset} className="weight-item">
                    <span className="asset-name">{asset}:</span>
                    <span className="weight-value">{(weight * 100).toFixed(2)}%</span>
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>
      )}
      
      {/* Performance Metrics */}
      {formatted.performance && (
        <div className="result-section">
          <h4>Performance Metrics</h4>
          <div className="metrics-grid">
            {Object.entries(formatted.performance).map(([metric, value]) => (
              <div key={metric} className="metric-item">
                <span className="metric-name">{metric}:</span>
                <span className="metric-value">{value}</span>
              </div>
            ))}
          </div>
        </div>
      )}
      
      {/* Quantum Results */}
      {formatted.quantum_result && (
        <div className="result-section">
          <h4>Quantum Optimization Details</h4>
          <div className="metrics-grid">
            {Object.entries(formatted.quantum_result).map(([metric, value]) => (
              <div key={metric} className="metric-item">
                <span className="metric-name">{metric}:</span>
                <span className="metric-value">{value}</span>
              </div>
            ))}
          </div>
        </div>
      )}
      
      {/* Fallback for unknown format */}
      {formatted.raw_data && (
        <div className="result-section">
          <h4>Raw Data</h4>
          <pre>{JSON.stringify(formatted.raw_data, null, 2)}</pre>
        </div>
      )}
    </div>
  );
};

function AppContent() {
  const { setLoading, isLoading } = useLoading();
  const [hybridOptResult, setHybridOptResult] = useState(null);
  const [dynamicOptResult, setDynamicOptResult] = useState(null);

  // Sample user for login validation
  const SAMPLE_USER = { username: 'demo', password: 'quantum123' };

  // Login form state
  const [login, setLogin] = useState({ username: '', password: '' });
  const [loginError, setLoginError] = useState('');
  const [loggedIn, setLoggedIn] = useState(false);
  const [authToken, setAuthToken] = useState('');

  // Transaction form state for amount only
  const [transaction, setTransaction] = useState({
    stockAmount: 2, // ultra-minimal stocks for fastest testing
    varPercent: 5, // default Value at Risk in %
    period: 10, // ultra-minimal days for fastest processing
    simulated: true, // default: simulated data
    qcSimulator: true, // default: use Aer quantum simulator
    // Speed preset selection
    optimizationSpeed: 'ultra-fast', // default to ultra-fast for testing
    // Dynamic Portfolio Optimization Parameters (ULTRA-optimized for fastest testing)
    numTimeSteps: 2, // minimal periods for meaningful results
    rebalanceFrequency: 7, // minimal days between rebalancing 
    riskAversion: 100, // lower risk aversion for faster convergence
    transactionFee: 0.01, // minimal transaction cost (0.01%)
    maxAllocation: 80, // higher max allocation for simpler constraints
    // Quantum Algorithm Parameters (ULTRA-optimized for sub-second execution)
    bitResolution: 1, // 1-bit resolution for minimal qubits
    numGenerations: 1, // absolute minimum: 1 generation
    populationSize: 2, // ultra-minimal population (DE minimum)
    estimatorShots: 10, // ultra-minimal shots for sub-second execution
    samplerShots: 50, // ultra-minimal shots for sub-second execution
    testMode: true // Enable ultra-fast test mode with classical approximation
  });
  const [optResult, setOptResult] = useState(null);
  const [transactionError, setTransactionError] = useState('');
  const [transactionSuccess, setTransactionSuccess] = useState('');
  
  // Async job management state
  const [activeJobId, setActiveJobId] = useState(null);
  const [jobStatus, setJobStatus] = useState(null);
  const [jobProgress, setJobProgress] = useState(0);
  const [jobStartTime, setJobStartTime] = useState(null);
  const [executionTime, setExecutionTime] = useState(0);
  const [stockData, setStockData] = useState([]); // [{symbol, date, close}]
  const [expandedStocks, setExpandedStocks] = useState({});
  const [lastSymbols, setLastSymbols] = useState([]);

  // Helper to generate random stock symbols
  const generateRandomStocks = (amount) => {
    const base = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'META', 'TSLA', 'NVDA', 'NFLX', 'INTC', 'IBM', 'ORCL', 'ADBE', 'CSCO', 'CRM', 'QCOM', 'TXN', 'AMD', 'AVGO', 'PYPL', 'SHOP'];
    let stocks = [];
    for (let i = 0; i < amount; i++) {
      // Use SIM_ prefix for simulator mode
      const baseSymbol = base[i % base.length] + (i >= base.length ? '_' + (i+1) : '');
      const symbol = 'SIM_' + baseSymbol;
      stocks.push(symbol);
    }
    return stocks;
  };

  // Simulate backend login and token issuance
  const fakeLoginApi = async (username, password) => {
    await new Promise((r) => setTimeout(r, 2000)); // Increased to 2 seconds to see spinner
    if (username === SAMPLE_USER.username && password === SAMPLE_USER.password) {
      return { success: true, token: 'sample-jwt-token-12345' };
    }
    return { success: false, message: 'Invalid credentials' };
  };

  // Real backend API call for stocks, returns historic data
    const realTransactionApi = async (data, token) => {
    try {
      const amount = Number(data.stockAmount) || 10;
      const period = Number(data.period) || 30;
      const stocks = generateRandomStocks(amount);
      setLastSymbols(stocks);
      const response = await fetch('/api/stocks/load', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          stocks,
          period,
          stockAmount: amount,
          symbols: stocks
        })
      });
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      const result = await response.json();
      return { success: true, data: result };
    } catch (error) {
      console.error('Stock loading failed:', error);
      return { 
        success: false, 
        message: `Failed to load stocks: ${error.message}` 
      };
    }
  };

  // Handlers
  const handleLoginChange = (e) => {
    setLogin({ ...login, [e.target.name]: e.target.value });
  };

  const handleLoginSubmit = async (e) => {
    e.preventDefault();
    setLoginError('');
    if (login.username && login.password) {
      setLoading('login', true, 'Authenticating...');
      const res = await fakeLoginApi(login.username, login.password);
      setLoading('login', false);
      if (res.success) {
        setLoggedIn(true);
        setAuthToken(res.token);
      } else {
        setLoginError(res.message);
      }
    } else {
      setLoginError('Please enter username and password.');
    }
  };

  const handleTransactionChange = (e) => {
    const { name, type, value, checked } = e.target;
    setTransaction({
      ...transaction,
      [name]: type === 'checkbox' ? checked : value
    });
  };

  const handleOptimizePortfolio = async (e) => {
    e.preventDefault();
    setOptResult(null);
    try {
      setLoading('optimizeClassic', true, 'Optimizing portfolio (classic)...');
      const response = await fetch('/api/stocks/optimize', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${authToken}`
        },
        body: JSON.stringify({
          stocks: lastSymbols,
          varPercent: Number(transaction.varPercent)
        })
      });
      setLoading('optimizeClassic', false);
      if (!response.ok) {
        const error = await response.json();
        setOptResult({ error: error.message || 'Backend error' });
        return;
      }
      const result = await response.json();
      setOptResult(result);
    } catch (err) {
      setLoading('optimizeClassic', false);
      setOptResult({ error: err.message });
    }
  };

      const handleHybridOptimizePortfolio = async () => {
    if (!lastSymbols.length) {
      setOptResult({ error: 'Please load stocks first' });
      return;
    }
    
    setLoading('optimizeHybrid', true);
    setOptResult(null);
    
    try {
      const response = await fetch('/api/stocks/hybrid-optimize', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${authToken}`
        },
        body: JSON.stringify({
          stocks: lastSymbols,
          varPercent: Number(transaction.varPercent),
          qcSimulator: transaction.qcSimulator
        })
      });
      
      setLoading('optimizeHybrid', false);
      if (!response.ok) {
        const error = await response.json();
        setOptResult({ error: error.message || 'Hybrid optimization failed' });
        return;
      }
      
      const result = await response.json();
      setHybridOptResult(result);
    } catch (error) {
      console.error('Error during hybrid optimization:', error);
      setHybridOptResult({ error: 'Network error during hybrid optimization' });
      setLoading('optimizeHybrid', false);
    }
  };

  // Async job polling function
  const pollJobStatus = async (jobId) => {
    try {
      const response = await fetch(`/api/stocks/dynamic-job/${jobId}/status`, {
        headers: {
          'Authorization': `Bearer ${authToken}`
        }
      });
      const data = await response.json();
      
      setJobStatus(data.status);
      setJobProgress(data.progress_percentage || 0);
      
      // Update execution time if job is running
      if (jobStartTime && (data.status === 'running' || data.status === 'completed')) {
        const currentTime = Date.now();
        const elapsed = (currentTime - jobStartTime) / 1000; // Convert to seconds
        setExecutionTime(elapsed);
      }
      
      if (data.status === 'completed') {
        // Fetch the actual result when job is completed
        try {
          const resultResponse = await fetch(`/api/stocks/dynamic-job/${jobId}/result`, {
            headers: {
              'Authorization': `Bearer ${authToken}`
            }
          });
          const resultData = await resultResponse.json();
          setDynamicOptResult(resultData);
          const finalExecutionTime = jobStartTime ? ((Date.now() - jobStartTime) / 1000).toFixed(2) : 'N/A';
          setTransactionSuccess(`Dynamic optimization completed successfully! Execution time: ${finalExecutionTime}s`);
        } catch (error) {
          console.error('Failed to fetch optimization result:', error);
          setTransactionError('Failed to retrieve optimization results');
        }
        setLoading('optimizeDynamic', false);
        setActiveJobId(null);
        return true; // Stop polling
      } else if (data.status === 'failed') {
        setTransactionError(data.error_message || 'Dynamic optimization failed');
        setLoading('optimizeDynamic', false);
        setActiveJobId(null);
        return true; // Stop polling
      }
      
      return false; // Continue polling
    } catch (error) {
      console.error('Job status check error:', error);
      return false;
    }
  };

  const handleDynamicOptimizePortfolio = async (e) => {
    e.preventDefault();
    setTransactionError('');
    setTransactionSuccess('');
    setJobStatus('starting');
    setJobProgress(0);
    setJobStartTime(Date.now()); // Track start time
    setExecutionTime(0);
    
    try {
      setLoading('optimizeDynamic', true, 'Starting dynamic optimization...');
      
      // Route through Java backend for consistency with classical/hybrid optimization
      const response = await fetch('/api/stocks/dynamic-optimize', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${authToken}`
        },
        body: JSON.stringify({
          stocks: lastSymbols,
          varPercent: Number(transaction.varPercent)
        })
      });
      
      const data = await response.json();
      
      if (response.ok && data.job_id) {
        setActiveJobId(data.job_id);
        setJobStatus('queued');
        setLoading('optimizeDynamic', true, 'Optimization queued, waiting for results...');
        
        // Start polling for results
        const pollInterval = setInterval(async () => {
          const shouldStop = await pollJobStatus(data.job_id);
          if (shouldStop) {
            clearInterval(pollInterval);
          }
        }, 2000); // Poll every 2 seconds
        
      } else {
        setTransactionError(data.error || 'Failed to start dynamic optimization');
        setLoading('optimizeDynamic', false);
      }
    } catch (error) {
      console.error('Dynamic optimization error:', error);
      setTransactionError(`Dynamic optimization failed: ${error.message}`);
      setLoading('optimizeDynamic', false);
    }
  };

  // Cancel active job function
  const cancelActiveJob = async () => {
    if (!activeJobId) return;
    
    try {
      const response = await fetch(`/api/stocks/dynamic-job/${activeJobId}/cancel`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${authToken}`
        }
      });
      
      if (response.ok) {
        setActiveJobId(null);
        setJobStatus('cancelled');
        setLoading('optimizeDynamic', false);
        setTransactionSuccess('Optimization cancelled successfully');
      }
    } catch (error) {
      console.error('Cancel job error:', error);
    }
  };

  const handleTransactionSubmit = async (e) => {
    e.preventDefault();
    setTransactionError('');
    setTransactionSuccess('');
    setStockData([]);
    if (transaction.stockAmount > 0) {
      setLoading('loadStocks', true, `Loading ${transaction.stockAmount} stocks...`);
      const res = await realTransactionApi(transaction, authToken);
      setLoading('loadStocks', false);
      if (res.success) {
        setTransactionSuccess('Stocks loaded and stored for optimization!');
        setStockData(res.data || []);
      } else {
        setTransactionError(res.message || 'Upload failed.');
      }
    } else {
      setTransactionError('Please enter a valid stock amount.');
    }
  };

  // --- Chart/grouping logic and collapsed state ---
  const sortedData = [...stockData].sort((a, b) => new Date(a.date) - new Date(b.date));
  const grouped = sortedData.reduce((acc, row) => {
    acc[row.symbol] = acc[row.symbol] || [];
    acc[row.symbol].push(row);
    return acc;
  }, {});
  const allDates = Array.from(new Set(sortedData.map(d => d.date))).sort();
  const datasets = Object.keys(grouped).map((symbol, idx) => ({
    label: symbol,
    data: allDates.map(date => {
      const found = grouped[symbol].find(d => d.date === date);
      return found ? found.close : null;
    }),
    borderColor: `hsl(${(idx * 40) % 360},70%,60%)`,
    backgroundColor: `hsla(${(idx * 40) % 360},70%,60%,0.2)`,
    tension: 0.2
  }));

  useEffect(() => {
    if (stockData.length > 0) {
      const initial = {};
      Object.keys(grouped).forEach(symbol => { initial[symbol] = false; });
      setExpandedStocks(initial);
    }
    // eslint-disable-next-line
  }, [stockData.length]);

  const handleToggle = (symbol) => {
    setExpandedStocks((prev) => ({ ...prev, [symbol]: !prev[symbol] }));
  };

  return (
    <div className="container">
      <h1>quantumFPO</h1>
      {!loggedIn ? (
        <form className="form login-form" onSubmit={handleLoginSubmit}>
          <h2>Login</h2>
          <input
            type="text"
            name="username"
            placeholder="Username (demo)"
            value={login.username}
            onChange={handleLoginChange}
            required
          />
          <input
            type="password"
            name="password"
            placeholder="Password (quantum123)"
            value={login.password}
            onChange={handleLoginChange}
            required
          />
          <button type="submit" disabled={isLoading('login')} style={{padding: '8px 16px', minWidth: '140px'}}>
            {isLoading('login') ? (
              <span style={{display: 'flex', alignItems: 'center', justifyContent: 'flex-start', paddingLeft: '16px', gap: '8px'}}>
                <BlochSpinner size={16} className="inline-spinner" />
                <span style={{fontSize: '0.9rem', whiteSpace: 'nowrap'}}>Auth...</span>
              </span>
            ) : (
              'Login'
            )}
          </button>
          {loginError && <p className="error">{loginError}</p>}
          <p style={{fontSize:'0.95rem',color:'#888'}}>Sample user: <b>demo</b> / <b>quantum123</b></p>
        </form>
      ) : (
        <form className="form portfolio-form" onSubmit={handleTransactionSubmit}>
          <div className="form-inputs-container">
            {/* Left Column: Load Stocks Configuration */}
            <div className="input-section load-stocks">
              <h3>📊 Stock Data Configuration</h3>
            <div>
              <label htmlFor="stockAmount" style={{display:'block',marginBottom:'4px'}}>Number of stocks to load</label>
              <input
                type="number"
                id="stockAmount"
                name="stockAmount"
                min="1"
                max="100"
                step="1"
                placeholder="Number of stocks to load"
                value={transaction.stockAmount}
                onChange={handleTransactionChange}
                required
              />
            </div>
            <div>
              <label htmlFor="period" style={{display:'block',marginBottom:'4px'}}>Number of days to load</label>
              <input
                type="number"
                id="period"
                name="period"
                min="5"
                max="365"
                step="5"
                placeholder="Number of days to load (10 for ultra-fast)"
                value={transaction.period}
                onChange={handleTransactionChange}
                title="Number of days of historical data to fetch (5-365, use 10 for ultra-fast testing)"
                required
              />
            </div>
            <div>
              <label htmlFor="varPercent" style={{display:'block',marginBottom:'4px'}}>Value at Risk (%)</label>
              <input
                type="number"
                id="varPercent"
                name="varPercent"
                min="1"
                max="100"
                step="0.1"
                placeholder="Value at Risk (%)"
                value={transaction.varPercent}
                onChange={handleTransactionChange}
                required
              />
            </div>
            <div>
              <label htmlFor="simulated" style={{display:'flex',alignItems:'center',gap:'8px',marginBottom:'4px'}}>
                <input
                  type="checkbox"
                  id="simulated"
                  name="simulated"
                  checked={transaction.simulated}
                  onChange={handleTransactionChange}
                />
                Simulated Data
              </label>
            </div>
            <div>
              <label htmlFor="qcSimulator" style={{display:'flex',alignItems:'center',gap:'8px',marginBottom:'4px'}}>
                <input
                  type="checkbox"
                  id="qcSimulator"
                  name="qcSimulator"
                  checked={transaction.qcSimulator}
                  onChange={handleTransactionChange}
                />
                QC Simulator (Aer)
              </label>
            </div>
          </div>

            {/* Middle Column: Dynamic Portfolio Optimization Parameters */}
            <div className="input-section dynamic-params">
              <h3>⚡ Dynamic Portfolio Parameters</h3>
              <div>
                <label htmlFor="numTimeSteps" style={{display:'block',marginBottom:'4px'}}>Number of Rebalancing Periods</label>
                <input
                  type="number"
                  id="numTimeSteps"
                  name="numTimeSteps"
                  min="2"
                  max="12"
                  step="1"
                  placeholder="Number of rebalancing periods"
                  value={transaction.numTimeSteps}
                  onChange={handleTransactionChange}
                  title="Number of time periods for dynamic rebalancing (2-12)"
                />
              </div>
              <div>
                <label htmlFor="rebalanceFrequency" style={{display:'block',marginBottom:'4px'}}>Rebalancing Frequency (days)</label>
                <input
                  type="number"
                  id="rebalanceFrequency"
                  name="rebalanceFrequency"
                  min="7"
                  max="90"
                  step="1"
                  placeholder="Days between rebalancing"
                  value={transaction.rebalanceFrequency}
                  onChange={handleTransactionChange}
                  title="Days between portfolio rebalancing (7-90)"
                />
              </div>
              <div>
                <label htmlFor="riskAversion" style={{display:'block',marginBottom:'4px'}}>Risk Aversion Coefficient</label>
                <input
                  type="number"
                  id="riskAversion"
                  name="riskAversion"
                  min="0"
                  max="10000"
                  step="100"
                  placeholder="Risk aversion coefficient"
                  value={transaction.riskAversion}
                  onChange={handleTransactionChange}
                  title="Higher values prefer lower-risk portfolios (0-10000)"
                />
              </div>
              <div>
                <label htmlFor="transactionFee" style={{display:'block',marginBottom:'4px'}}>Transaction Cost Rate (%)</label>
                <input
                  type="number"
                  id="transactionFee"
                  name="transactionFee"
                  min="0"
                  max="10"
                  step="0.01"
                  placeholder="Transaction cost rate"
                  value={transaction.transactionFee}
                  onChange={handleTransactionChange}
                  title="Transaction cost as percentage (0-10%)"
                />
              </div>
              <div>
                <label htmlFor="maxAllocation" style={{display:'block',marginBottom:'4px'}}>Max Allocation per Asset (%)</label>
                <input
                  type="number"
                  id="maxAllocation"
                  name="maxAllocation"
                  min="10"
                  max="100"
                  step="5"
                  placeholder="Maximum allocation percentage"
                  value={transaction.maxAllocation}
                  onChange={handleTransactionChange}
                  title="Maximum allocation percentage per asset (10-100%)"
                />
              </div>
            </div>

            {/* Right Column: Quantum Algorithm Parameters */}
            <div className="input-section quantum-params">
              <h3>🔬 Quantum Algorithm Parameters</h3>
              <div>
                <label htmlFor="bitResolution" style={{display:'block',marginBottom:'4px'}}>Allocation Bit Resolution</label>
                <input
                  type="number"
                  id="bitResolution"
                  name="bitResolution"
                  min="1"
                  max="4"
                  step="1"
                  placeholder="Bits per allocation variable"
                  value={transaction.bitResolution}
                  onChange={handleTransactionChange}
                  title="Number of qubits per asset allocation (higher = more precision)"
                />
              </div>
              <div>
                <label htmlFor="numGenerations" style={{display:'block',marginBottom:'4px'}}>Optimization Generations</label>
                <input
                  type="number"
                  id="numGenerations"
                  name="numGenerations"
                  min="1"
                  max="20"
                  step="1"
                  placeholder="Differential evolution generations"
                  value={transaction.numGenerations}
                  onChange={handleTransactionChange}
                  title="Number of optimization generations (1-20, use 1 for ultra-fast testing)"
                />
              </div>
              <div>
                <label htmlFor="populationSize" style={{display:'block',marginBottom:'4px'}}>Population Size</label>
                <input
                  type="number"
                  id="populationSize"
                  name="populationSize"
                  min="2"
                  max="50"
                  step="1"
                  placeholder="Population size"
                  value={transaction.populationSize}
                  onChange={handleTransactionChange}
                  title="Differential evolution population size (2-50, use 2 for ultra-fast testing)"
                />
              </div>
              <div>
                <label htmlFor="estimatorShots" style={{display:'block',marginBottom:'4px'}}>Quantum Estimator Shots</label>
                <input
                  type="number"
                  id="estimatorShots"
                  name="estimatorShots"
                  min="10"
                  max="10000"
                  step="10"
                  placeholder="Estimator shots"
                  value={transaction.estimatorShots}
                  onChange={handleTransactionChange}
                  title="Number of shots for quantum expectation value estimation (10 for ultra-fast testing)"
                />
              </div>
              <div>
                <label htmlFor="samplerShots" style={{display:'block',marginBottom:'4px'}}>Quantum Sampler Shots</label>
                <input
                  type="number"
                  id="samplerShots"
                  name="samplerShots"
                  min="50"
                  max="50000"
                  step="50"
                  placeholder="Sampler shots"
                  value={transaction.samplerShots}
                  onChange={handleTransactionChange}
                  title="Number of shots for quantum sampling (50 for ultra-fast testing)"
                />
              </div>
            </div>
          </div>
          
          {/* Speed Presets and Action Buttons */}
          <div className="form-actions-container">
            <div style={{display: 'flex', gap: '2rem', alignItems: 'flex-start', flexWrap: 'wrap'}}>
              {/* Optimization Speed Presets */}
              <div style={{flex: '2', minWidth: '400px', padding: '20px', backgroundColor: '#f8f9fa', borderRadius: '12px', border: '1px solid #e9ecef'}}>
                <h4 style={{margin: '0 0 20px 0', color: '#7c3aed', fontSize: '1.2rem', textAlign: 'center'}}>⚡ Optimization Speed Presets</h4>
              <div style={{display: 'flex', flexDirection: 'row', gap: '15px', justifyContent: 'space-around', flexWrap: 'wrap'}}>
                
                {/* Ultra-Fast Radio Button */}
                <label style={{display: 'flex', alignItems: 'flex-start', gap: '12px', cursor: 'pointer', padding: '15px', borderRadius: '8px', border: '2px solid transparent', transition: 'all 0.2s', flex: '1', minWidth: '250px'}}
                       className={transaction.optimizationSpeed === 'ultra-fast' ? 'speed-preset-selected' : 'speed-preset'}
                       onClick={() => {
                         setTransaction(prev => ({
                           ...prev,
                           optimizationSpeed: 'ultra-fast',
                           numGenerations: 1,
                           populationSize: 2,
                           estimatorShots: 10,
                           samplerShots: 50,
                           numTimeSteps: 2,
                           period: 10,
                           stockAmount: 2,
                           testMode: true
                         }))
                       }}>
                  <input
                    type="radio"
                    name="optimizationSpeed"
                    value="ultra-fast"
                    checked={transaction.optimizationSpeed === 'ultra-fast'}
                    onChange={() => {}}
                    style={{marginTop: '2px', transform: 'scale(1.3)'}}
                  />
                  <div>
                    <div style={{fontWeight: '600', color: '#28a745', marginBottom: '8px', fontSize: '1rem'}}>🚀 Ultra-Fast (~0.01s)</div>
                    <div style={{fontSize: '0.85rem', color: '#6c757d', lineHeight: '1.4'}}>
                      Test mode with classical approximation<br/>
                      <strong>Parameters:</strong> 1 gen, 2 pop, 10/50 shots
                    </div>
                  </div>
                </label>

                {/* Fast Radio Button */}
                <label style={{display: 'flex', alignItems: 'flex-start', gap: '12px', cursor: 'pointer', padding: '15px', borderRadius: '8px', border: '2px solid transparent', transition: 'all 0.2s', flex: '1', minWidth: '250px'}}
                       className={transaction.optimizationSpeed === 'fast' ? 'speed-preset-selected' : 'speed-preset'}
                       onClick={() => {
                         setTransaction(prev => ({
                           ...prev,
                           optimizationSpeed: 'fast',
                           numGenerations: 5,
                           populationSize: 10,
                           estimatorShots: 100,
                           samplerShots: 500,
                           numTimeSteps: 3,
                           period: 30,
                           stockAmount: 3,
                           testMode: false
                         }))
                       }}>
                  <input
                    type="radio"
                    name="optimizationSpeed"
                    value="fast"
                    checked={transaction.optimizationSpeed === 'fast'}
                    onChange={() => {}}
                    style={{marginTop: '2px', transform: 'scale(1.3)'}}
                  />
                  <div>
                    <div style={{fontWeight: '600', color: '#ffc107', marginBottom: '8px', fontSize: '1rem'}}>⚡ Fast (~10-30s)</div>
                    <div style={{fontSize: '0.85rem', color: '#6c757d', lineHeight: '1.4'}}>
                      Real quantum optimization, minimal params<br/>
                      <strong>Parameters:</strong> 5 gen, 10 pop, 100/500 shots
                    </div>
                  </div>
                </label>

                {/* Normal Radio Button */}
                <label style={{display: 'flex', alignItems: 'flex-start', gap: '12px', cursor: 'pointer', padding: '15px', borderRadius: '8px', border: '2px solid transparent', transition: 'all 0.2s', flex: '1', minWidth: '250px'}}
                       className={transaction.optimizationSpeed === 'normal' ? 'speed-preset-selected' : 'speed-preset'}
                       onClick={() => {
                         setTransaction(prev => ({
                           ...prev,
                           optimizationSpeed: 'normal',
                           numGenerations: 20,
                           populationSize: 40,
                           estimatorShots: 1000,
                           samplerShots: 5000,
                           numTimeSteps: 4,
                           period: 90,
                           stockAmount: 5,
                           testMode: false
                         }))
                       }}>
                  <input
                    type="radio"
                    name="optimizationSpeed"
                    value="normal"
                    checked={transaction.optimizationSpeed === 'normal'}
                    onChange={() => {}}
                    style={{marginTop: '2px', transform: 'scale(1.3)'}}
                  />
                  <div>
                    <div style={{fontWeight: '600', color: '#dc3545', marginBottom: '8px', fontSize: '1rem'}}>🎯 Normal (~2-5min)</div>
                    <div style={{fontSize: '0.85rem', color: '#6c757d', lineHeight: '1.4'}}>
                      Full quantum optimization, production params<br/>
                      <strong>Parameters:</strong> 20 gen, 40 pop, 1K/5K shots
                    </div>
                  </div>
                </label>
                
              </div>
                <p style={{margin: '20px 0 0 0', fontSize: '0.9rem', color: '#6c757d', fontStyle: 'italic', textAlign: 'center'}}>
                  💡 Select a preset to automatically configure all optimization parameters for different speed/accuracy trade-offs.
                </p>
              </div>

              {/* Action Buttons */}
              <div style={{flex: '1', minWidth: '300px', padding: '20px', backgroundColor: '#f8f9fa', borderRadius: '12px', border: '1px solid #e9ecef'}}>
                <h4 style={{margin: '0 0 20px 0', color: '#28a745', fontSize: '1.2rem', textAlign: 'center'}}>🎯 Portfolio Actions</h4>
                <div className="form-buttons" style={{flexDirection: 'column', gap: '1rem'}}>
            <button type="submit" disabled={isLoading('loadStocks')}>
              {isLoading('loadStocks') ? (
                <>
                  <BlochSpinner size={16} className="inline-spinner" />
                  Loading...
                </>
              ) : (
                'Load Stocks'
              )}
            </button>
            <button type="button" onClick={handleOptimizePortfolio} disabled={isLoading('optimizeClassic')}>
              {isLoading('optimizeClassic') ? (
                <>
                  <BlochSpinner size={16} className="inline-spinner" />
                  Optimizing...
                </>
              ) : (
                'Optimize Portfolio Classic'
              )}
            </button>
            <button type="button" style={{background:'#6c47ff'}} onClick={handleHybridOptimizePortfolio} disabled={isLoading('optimizeHybrid')}>
              {isLoading('optimizeHybrid') ? (
                <>
                  <BlochSpinner size={16} className="inline-spinner" />
                  Optimizing...
                </>
              ) : (
                'Optimize Portfolio Hybrid'
              )}
            </button>
            <button type="button" style={{background:'#ff6b47'}} onClick={handleDynamicOptimizePortfolio} disabled={isLoading('optimizeDynamic')}>
              {isLoading('optimizeDynamic') ? (
                <>
                  <BlochSpinner size={16} className="inline-spinner" />
                  Optimizing...
                </>
              ) : (
                'Optimize Portfolio Dynamic'
              )}
            </button>
            
                {/* Cancel button for active jobs */}
                {activeJobId && jobStatus !== 'completed' && jobStatus !== 'failed' && (
                  <button 
                    type="button" 
                    style={{background:'#dc3545', marginLeft: '10px', color: 'white'}} 
                    onClick={cancelActiveJob}
                  >
                    Cancel Job
                  </button>
                )}
                </div>
              </div>
            </div>
          </div>
          
          {/* Job Status Display */}
          {activeJobId && (
            <div className="job-status-display" style={{
              margin: '15px 0',
              padding: '15px',
              border: '1px solid #ddd',
              borderRadius: '8px',
              backgroundColor: '#f8f9fa'
            }}>
              <h4 style={{margin: '0 0 10px 0', color: '#333'}}>
                Optimization Status: {jobStatus}
              </h4>
              <div style={{marginBottom: '10px'}}>
                <strong>Job ID:</strong> {activeJobId}
              </div>
              <div style={{marginBottom: '10px'}}>
                <strong>Progress:</strong> {jobProgress}%
              </div>
              <div style={{marginBottom: '10px'}}>
                <strong>Execution Time:</strong> {executionTime.toFixed(2)}s
              </div>
              <div style={{marginBottom: '10px'}}>
                <strong>Speed Preset:</strong> 
                <span style={{
                  marginLeft: '8px',
                  padding: '2px 8px',
                  borderRadius: '4px',
                  fontSize: '0.85rem',
                  backgroundColor: transaction.optimizationSpeed === 'ultra-fast' ? '#d4edda' : 
                                   transaction.optimizationSpeed === 'fast' ? '#fff3cd' : '#f8d7da',
                  color: transaction.optimizationSpeed === 'ultra-fast' ? '#155724' : 
                         transaction.optimizationSpeed === 'fast' ? '#856404' : '#721c24'
                }}>
                  {transaction.optimizationSpeed === 'ultra-fast' ? '🚀 Ultra-Fast' : 
                   transaction.optimizationSpeed === 'fast' ? '⚡ Fast' : '🎯 Normal'}
                </span>
              </div>
              <div className="progress-bar" style={{
                width: '100%',
                height: '20px',
                backgroundColor: '#e0e0e0',
                borderRadius: '10px',
                overflow: 'hidden'
              }}>
                <div 
                  className="progress-fill" 
                  style={{
                    width: `${jobProgress}%`,
                    height: '100%',
                    backgroundColor: jobStatus === 'running' ? '#28a745' : '#6c757d',
                    transition: 'width 0.3s ease'
                  }}
                />
              </div>
              {jobStatus === 'running' && (
                <div style={{marginTop: '10px', fontSize: '0.9em', color: '#666'}}>
                  ⚡ Quantum optimization in progress... This may take several minutes.
                </div>
              )}
            </div>
          )}
        </form>
      )}
      
      {/* Form Messages */}
      {loggedIn && (transactionError || transactionSuccess) && (
        <div className="form-messages">
          {transactionError && <p className="error">{transactionError}</p>}
          {transactionSuccess && <p className="success">{transactionSuccess}</p>}
        </div>
      )}
      
      {/* Combined Optimization Results Section */}
      {loggedIn && (optResult || hybridOptResult || dynamicOptResult) && (
        <div className="optimization-results-section">
          <h2>Portfolio Optimization Results</h2>
          <div className="optimization-results-container">
            {optResult && (
              <div className="optimization-result classic-result">
                <OptimizationResultDisplay 
                  result={optResult} 
                  type="classic" 
                  title="Classic Optimization Result" 
                />
              </div>
            )}
            {hybridOptResult && (
              <div className="optimization-result hybrid-result">
                <OptimizationResultDisplay 
                  result={hybridOptResult} 
                  type="hybrid" 
                  title="Hybrid Quantum Optimization Result" 
                />
              </div>
            )}
            {dynamicOptResult && (
              <div className="optimization-result dynamic-result">
                <OptimizationResultDisplay 
                  result={dynamicOptResult} 
                  type="dynamic" 
                  title="Dynamic Quantum Optimization Result" 
                />
              </div>
            )}
          </div>
        </div>
      )}
      {loggedIn && stockData.length > 0 && (
        <div className="stock-data-container">
          <div className="chart-container">
            <h2>All Stock Data (Combined Chart)</h2>
            <Line
              data={{
                labels: allDates,
                datasets
              }}
              options={{
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                  legend: { position: 'top' },
                  title: { display: true, text: 'All Stocks - Historic Price Data' }
                },
                scales: {
                  x: { title: { display: true, text: 'Date' } },
                  y: { title: { display: true, text: 'Price ($)' } }
                }
              }}
              height={400}
            />
          </div>
          <h2>Historic Stock Data</h2>
          {Object.keys(grouped).map((symbol) => {
            const data = grouped[symbol];
            const expanded = expandedStocks[symbol] ?? false;
            return (
              <div key={symbol} className="stock-item">
                <div className="stock-header">
                  <h3 style={{margin: 0}}>{symbol}</h3>
                  <button className="expand-btn" onClick={() => handleToggle(symbol)}>
                    {expanded ? '▼ Hide History' : '▶ Show History'}
                  </button>
                </div>
                {expanded && (
                  <table className="stock-table">
                    <thead>
                      <tr>
                        <th>Date</th>
                        <th>Close Price ($)</th>
                      </tr>
                    </thead>
                    <tbody>
                      {data.map((row) => (
                        <tr key={`${row.symbol}-${row.date}`}>
                          <td>{row.date}</td>
                          <td>${Number(row.close).toFixed(2)}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}

function App() {
  return (
    <LoadingProvider>
      <AppContent />
    </LoadingProvider>
  );
}

export default App;