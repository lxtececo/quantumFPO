import React, { useState } from 'react';
import { Line } from 'react-chartjs-2';
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

function App() {
  // Sample user for login validation
  const SAMPLE_USER = { username: 'demo', password: 'quantum123' };

  // Login form state
  const [login, setLogin] = useState({ username: '', password: '' });
  const [loginError, setLoginError] = useState('');
  const [loggedIn, setLoggedIn] = useState(false);
  const [authToken, setAuthToken] = useState('');

  // Transaction form state for three stocks
  const [transaction, setTransaction] = useState({
    stock1: 'SIM_APPL',
    stock2: 'SIM_MSFT',
    stock3: 'SIM_GOOGL',
    varPercent: 5 // default Value at Risk in %
  });
  const [optResult, setOptResult] = useState(null);
  const [transactionError, setTransactionError] = useState('');
  const [transactionSuccess, setTransactionSuccess] = useState('');
  const [stockData, setStockData] = useState([]); // [{symbol, date, close}]
  const [expandedStocks, setExpandedStocks] = useState({});

  // Simulate backend login and token issuance
  const fakeLoginApi = async (username, password) => {
    // Simulate network delay
    await new Promise((r) => setTimeout(r, 500));
    if (username === SAMPLE_USER.username && password === SAMPLE_USER.password) {
      // Return a fake JWT token
      return { success: true, token: 'sample-jwt-token-12345' };
    }
    return { success: false, message: 'Invalid credentials' };
  };

  // Real backend API call for three stocks, returns historic data
  const realTransactionApi = async (data, token) => {
    try {
      const response = await fetch('http://localhost:8080/api/stocks/load', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          stocks: [data.stock1, data.stock2, data.stock3],
          period: 30 // last 30 days
        })
      });
      if (!response.ok) {
        const error = await response.json();
        return { success: false, message: error.message || 'Backend error' };
      }
      // Expect backend to return all stock data as [{symbol, date, close}]
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
    // Secure login: call backend and get token
    if (login.username && login.password) {
      const res = await fakeLoginApi(login.username, login.password);
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
    setTransaction({ ...transaction, [e.target.name]: e.target.value });
  };

  // Call backend optimization API
  const handleOptimizePortfolio = async (e) => {
    e.preventDefault();
    setOptResult(null);
    try {
      const response = await fetch('http://localhost:8080/api/stocks/optimize', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${authToken}`
        },
        body: JSON.stringify({
          stocks: [transaction.stock1, transaction.stock2, transaction.stock3],
          varPercent: Number(transaction.varPercent)
        })
      });
      if (!response.ok) {
        const error = await response.json();
        setOptResult({ error: error.message || 'Backend error' });
        return;
      }
      const result = await response.json();
      setOptResult(result);
    } catch (err) {
      setOptResult({ error: err.message });
    }
  };

  const handleTransactionSubmit = async (e) => {
    e.preventDefault();
    setTransactionError('');
    setTransactionSuccess('');
    setStockData([]);
    if (transaction.stock1 && transaction.stock2 && transaction.stock3) {
      // Real backend: send token in request
      const res = await realTransactionApi(transaction, authToken);
      if (res.success) {
        setTransactionSuccess('Stocks loaded and stored for optimization!');
        setStockData(res.data || []);
      } else {
        setTransactionError(res.message || 'Upload failed.');
      }
    } else {
      setTransactionError('Please enter all three stock names.');
    }
  };

  return (
    <div className="container">
      <h1>Quantum Portfolio Optimization</h1>
      {!loggedIn ? (
        <form className="form" onSubmit={handleLoginSubmit}>
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
          <button type="submit">Login</button>
          {loginError && <p className="error">{loginError}</p>}
          <p style={{fontSize:'0.95rem',color:'#888'}}>Sample user: <b>demo</b> / <b>quantum123</b></p>
        </form>
      ) : (
        <form className="form" onSubmit={handleTransactionSubmit}>
          <h2>Load Stocks for Portfolio</h2>
          <input
            type="text"
            name="stock1"
            placeholder="Stock Name 1 (e.g. AAPL)"
            value={transaction.stock1}
            onChange={handleTransactionChange}
            required
          />
          <input
            type="text"
            name="stock2"
            placeholder="Stock Name 2 (e.g. MSFT)"
            value={transaction.stock2}
            onChange={handleTransactionChange}
            required
          />
          <input
            type="text"
            name="stock3"
            placeholder="Stock Name 3 (e.g. GOOGL)"
            value={transaction.stock3}
            onChange={handleTransactionChange}
            required
          />
          <input
            type="number"
            name="varPercent"
            min="1"
            max="100"
            step="0.1"
            placeholder="Value at Risk (%)"
            value={transaction.varPercent}
            onChange={handleTransactionChange}
            required
            style={{marginBottom:'8px'}}
          />
          <button type="submit">Load Stocks</button>
          <button type="button" style={{marginLeft:'10px'}} onClick={handleOptimizePortfolio}>Optimize Portfolio</button>
          {transactionError && <p className="error">{transactionError}</p>}
          {transactionSuccess && <p className="success">{transactionSuccess}</p>}
          {optResult && (
            <div style={{marginTop:'10px'}}>
              {optResult.error ? (
                <p className="error">{optResult.error}</p>
              ) : (
                <div>
                  <h3>Optimization Result</h3>
                  <pre>{JSON.stringify(optResult, null, 2)}</pre>
                </div>
              )}
            </div>
          )}
        </form>
      )}
      {loggedIn && stockData.length > 0 && (() => {
        const sortedData = [...stockData].sort((a, b) => new Date(a.date) - new Date(b.date));
        // Group data by symbol
        const grouped = sortedData.reduce((acc, row) => {
          acc[row.symbol] = acc[row.symbol] || [];
          acc[row.symbol].push(row);
          return acc;
        }, {});
        const handleToggle = (symbol) => {
          setExpandedStocks((prev) => ({ ...prev, [symbol]: !prev[symbol] }));
        };
        return (
          <div style={{marginTop: '2rem'}}>
            <h2>Historic Stock Data</h2>
            {Object.keys(grouped).map((symbol) => {
              const data = grouped[symbol];
              const expanded = expandedStocks[symbol];
              return (
                <div key={symbol} style={{marginBottom: '2rem', border: '1px solid #eee', borderRadius: '8px', padding: '1rem'}}>
                  <div style={{display: 'flex', alignItems: 'center', justifyContent: 'space-between'}}>
                    <h3 style={{margin: 0}}>{symbol}</h3>
                    <button className="expand-btn" onClick={() => handleToggle(symbol)}>
                      {expanded ? '▼ Hide History' : '▶ Show History'}
                    </button>
                  </div>
                  {expanded && (
                    <table style={{width: '100%', borderCollapse: 'collapse', marginTop: '1rem'}}>
                      <thead>
                        <tr>
                          <th style={{borderBottom: '1px solid #ccc'}}>Date</th>
                          <th style={{borderBottom: '1px solid #ccc'}}>Open</th>
                          <th style={{borderBottom: '1px solid #ccc'}}>High</th>
                          <th style={{borderBottom: '1px solid #ccc'}}>Low</th>
                          <th style={{borderBottom: '1px solid #ccc'}}>Close</th>
                        </tr>
                      </thead>
                      <tbody>
                        {data.map((row) => (
                          <tr key={`${row.symbol}-${row.date}`}>
                            <td>{row.date}</td>
                            <td>{row.open}</td>
                            <td>{row.high}</td>
                            <td>{row.low}</td>
                            <td>{row.close}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  )}
                  <div style={{marginTop: '2rem'}}>
                    <Line
                      data={{
                        labels: data.map(d => d.date),
                        datasets: [
                          {
                            label: `${symbol} Open`,
                            data: data.map(d => d.open),
                            borderColor: '#ffa600',
                            backgroundColor: 'rgba(255,166,0,0.1)',
                            tension: 0.2
                          },
                          {
                            label: `${symbol} High`,
                            data: data.map(d => d.high),
                            borderColor: '#00c49a',
                            backgroundColor: 'rgba(0,196,154,0.1)',
                            tension: 0.2
                          },
                          {
                            label: `${symbol} Low`,
                            data: data.map(d => d.low),
                            borderColor: '#ff6361',
                            backgroundColor: 'rgba(255,99,97,0.1)',
                            tension: 0.2
                          },
                          {
                            label: `${symbol} Close`,
                            data: data.map(d => d.close),
                            borderColor: '#4da6ff',
                            backgroundColor: 'rgba(77,166,255,0.2)',
                            tension: 0.2
                          }
                        ]
                      }}
                      options={{
                        responsive: true,
                        plugins: {
                          legend: { position: 'top' },
                          title: { display: true, text: `${symbol} - Last 30 Days` }
                        },
                        scales: {
                          x: { title: { display: true, text: 'Date' } },
                          y: { title: { display: true, text: 'Price' } }
                        }
                      }}
                    />
                  </div>
                </div>
              );
            })}
          </div>
        );
      })()}
    </div>
  );
}

export default App;
