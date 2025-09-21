
# Quantum Financial Portfolio Optimization (quantumFPO)

## Project Overview
This project is a full-stack application for quantum-inspired financial portfolio optimization. It features a fast JavaScript frontend (React + Vite), a Spring Boot backend for RESTful services, and a Python microservice for advanced portfolio optimization using PyPortfolioOpt.

### Main Features
- **User Login**: Secure login form for user authentication.
- **Stock Data Loader**: Form to input up to three stock symbols and a Value at Risk (VaR) percentage.
- **Historic Data Visualization**: Table and interactive chart displaying open, high, low, and close prices for each stock.
- **Portfolio Optimization**: Backend service integrates with Python to compute optimal portfolio weights using mean-variance optimization (max Sharpe ratio).
- **Mock Data Support**: Simulate stock data for development/testing using special stock symbols (e.g., SIM_APPL).

---

## Quick Setup Instructions


### Prerequisites
- Node.js (v18+ recommended)
- Java (JDK 17+ recommended)
- Python (3.8+ recommended)
- Git
- [Scoop](https://scoop.sh/#/) (recommended Windows command line installer)

#### Install Scoop (Windows)
Open PowerShell and run:
```powershell
iwr -useb get.scoop.sh | iex
```
See [Scoop documentation](https://scoop.sh/#/) for details.

#### Install Maven with Scoop
```powershell
scoop install maven
```
See [Scoop Maven page](https://scoop.sh/#/apps?q=maven) for more info.

### 1. Clone the Repository
```sh
git clone https://github.com/lxtececo/quantumFPO.git
cd quantumFPO
```

### 2. Install Frontend Dependencies
```sh
cd quantumFPO
npm install
```

### 3. Start the Frontend (React + Vite)
```sh
npm run dev
```
Frontend will run at [http://localhost:5173](http://localhost:5173).

### 4. Setup Python Environment
```sh
cd backend/src/main/python
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt  # Or manually: pip install pypfopt pandas numpy scikit-learn
```

### 5. Start the Spring Boot Backend
```sh
cd ../../../..
./mvnw spring-boot:run  # Or use your IDE to run StocksApplication
```
Backend will run at [http://localhost:8080](http://localhost:8080).

---

## Usage
1. **Login** with sample credentials (`demo` / `quantum123`).
2. **Enter stock symbols** (e.g., SIM_APPL, SIM_MSFT, SIM_GOOGL) and VaR percentage.
3. **Load stocks** to view historic data and charts.
4. **Optimize portfolio** to get risk-adjusted weights and performance metrics.

---

## Notes
- For development, use `SIM_` prefixed stock symbols to generate mock data and avoid API limits.
- The backend integrates with Alpha Vantage for real stock data (API key required in `application.properties`).
- Portfolio optimization is performed using PyPortfolioOpt in Python, called from the Java backend.

---

## Python Library: PyPortfolioOpt
This project uses [PyPortfolioOpt](https://pyportfolioopt.readthedocs.io/en/latest/UserGuide.html#user-guide), a popular open-source Python library for financial portfolio optimization. PyPortfolioOpt provides:
- Mean-variance optimization (Markowitz model)
- Maximization of Sharpe ratio (risk-adjusted return)
- Support for constraints and advanced risk models
- Integration with pandas for easy data handling

For more details, see the [PyPortfolioOpt User Guide](https://pyportfolioopt.readthedocs.io/en/latest/UserGuide.html#user-guide).

---

## License
MIT
