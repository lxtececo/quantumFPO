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

function AppContent() {
  const { setLoading, isLoading } = useLoading();
  const [hybridOptResult, setHybridOptResult] = useState(null);

  // Sample user for login validation
  const SAMPLE_USER = { username: 'demo', password: 'quantum123' };

  // Login form state
  const [login, setLogin] = useState({ username: '', password: '' });
  const [loginError, setLoginError] = useState('');
  const [loggedIn, setLoggedIn] = useState(false);
  const [authToken, setAuthToken] = useState('');

  // Transaction form state for amount only
  const [transaction, setTransaction] = useState({
    stockAmount: 10, // default number of stocks to load
    varPercent: 5, // default Value at Risk in %
    period: 30, // default number of days to load
    simulated: true, // default: simulated data
    qcSimulator: true // default: use Aer quantum simulator
  });
  const [optResult, setOptResult] = useState(null);
  const [transactionError, setTransactionError] = useState('');
  const [transactionSuccess, setTransactionSuccess] = useState('');
  const [stockData, setStockData] = useState([]); // [{symbol, date, close}]
  const [expandedStocks, setExpandedStocks] = useState({});
  const [lastSymbols, setLastSymbols] = useState([]);

  // Helper to generate random stock symbols
  const generateRandomStocks = (amount) => {
    const base = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'META', 'TSLA', 'NVDA', 'NFLX', 'INTC', 'IBM', 'ORCL', 'ADBE', 'CSCO', 'CRM', 'QCOM', 'TXN', 'AMD', 'AVGO', 'PYPL', 'SHOP'];
    let stocks = [];
    for (let i = 0; i < amount; i++) {
      // Use SIM_ prefix for simulator mode
      const symbol = base[i % base.length] + (i >= base.length ? '_' + (i+1) : '');
      stocks.push('SIM_' + symbol);
    }
    return stocks;
  };

  // Simulate backend login and token issuance
  const fakeLoginApi = async (username, password) => {
    await new Promise((r) => setTimeout(r, 500));
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
          simulated: data.simulated
        })
      });
      if (!response.ok) {
        const error = await response.json();
        return { success: false, message: error.message || 'Backend error' };
      }
      const result = await response.json();
      return { success: true, data: result };
    } catch (err) {
      return { success: false, message: err.message };
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

  const handleHybridOptimizePortfolio = async (e) => {
    e.preventDefault();
    setHybridOptResult(null);
    try {
      setLoading('optimizeHybrid', true, 'Optimizing portfolio (quantum hybrid)...');
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
        setHybridOptResult({ error: error.message || 'Backend error' });
        return;
      }
      const result = await response.json();
      setHybridOptResult(result);
    } catch (err) {
      setLoading('optimizeHybrid', false);
      setHybridOptResult({ error: err.message });
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
          <button type="submit" disabled={isLoading('login')}>
            {isLoading('login') ? (
              <>
                <BlochSpinner size={16} className="inline-spinner" />
                Authenticating...
              </>
            ) : (
              'Login'
            )}
          </button>
          {loginError && <p className="error">{loginError}</p>}
          <p style={{fontSize:'0.95rem',color:'#888'}}>Sample user: <b>demo</b> / <b>quantum123</b></p>
        </form>
      ) : (
        <form className="form portfolio-form" onSubmit={handleTransactionSubmit}>
          <div className="form-inputs">
            <h2>Load Stocks for Portfolio</h2>
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
                min="1"
                max="365"
                step="1"
                placeholder="Number of days to load"
                value={transaction.period}
                onChange={handleTransactionChange}
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
          <div className="form-buttons">
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
          </div>
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
      {loggedIn && (optResult || hybridOptResult) && (
        <div className="optimization-results-section">
          <h2>Portfolio Optimization Results</h2>
          <div className="optimization-results-container">
            {optResult && (
              <div className="optimization-result classic-result">
                {optResult.error ? (
                  <div>
                    <h3>Classic Optimization Result</h3>
                    <p className="error">{optResult.error}</p>
                  </div>
                ) : (
                  <div>
                    <h3>Classic Optimization Result</h3>
                    <pre>{JSON.stringify(optResult, null, 2)}</pre>
                  </div>
                )}
              </div>
            )}
            {hybridOptResult && (
              <div className="optimization-result hybrid-result">
                {hybridOptResult.error ? (
                  <div>
                    <h3>Hybrid Quantum Optimization Result</h3>
                    <p className="error">{hybridOptResult.error}</p>
                  </div>
                ) : (
                  <div>
                    <h3>Hybrid Quantum Optimization Result</h3>
                    <pre>{JSON.stringify(hybridOptResult, null, 2)}</pre>
                  </div>
                )}
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