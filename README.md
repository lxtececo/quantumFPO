
# Quantum Financial Portfolio Optimization (quantumFPO)

## Project Overview
This project is a full-stack application for quantum-inspired financial portfolio optimization. It features a fast JavaScript frontend (React + Vite), a Spring Boot backend for RESTful services, and a Python microservice for advanced portfolio optimization using PyPortfolioOpt.



### Main Features & Enhancements
- **User Login**: Secure login form for user authentication.
- **Dynamic Stock Amount**: Input field for stock amount lets users request any number of stocks. The frontend generates a random list of stock symbols and passes it to the backend for simulation or real data retrieval.
- **Flexible Period Selection**: Users can select the number of days of historical data to load for optimization.
- **Historic Data Visualization**: Table and interactive chart displaying open, high, low, and close prices for each stock.
- **Portfolio Optimization**: Backend service integrates with Python to compute optimal portfolio weights using mean-variance optimization (max Sharpe ratio).
- **Quantum Optimization (QAOA)**: Python backend supports quantum-inspired optimization using Qiskit QAOA, AerSimulator, and IBM Quantum backends. Includes job tracking and detailed logging for quantum jobs.
- **Robust Logging & Error Handling**: All backend and Python optimizer scripts include step-by-step logging, error handling, and job tracking for debugging and transparency.
- **Mock Data Support**: Simulate stock data for development/testing using special stock symbols (e.g., SIM_APPL).
- **Full-Stack Test Coverage**: Unit and integration tests for frontend (Jest/Testing Library), backend (JUnit/Spring Boot Test), and Python microservices (pytest).

---

## Future Enhancements
- Explore Quantum diagonalization algorithms. [Learn more](https://qiskit.qotlabs.org/learning/courses/quantum-diagonalization-algorithms)
- Explore The variational quantum eigensolver (VQE) for financial optimization. [Learn more](https://qiskit.qotlabs.org/learning/courses/quantum-diagonalization-algorithms/vqe)
- Explore Perform dynamic portfolio optimization with Global Data Quantum's Portfolio Optimizer. [Learn more](https://quantum.cloud.ibm.com/docs/en/tutorials/global-data-quantum-optimizer#perform-dynamic-portfolio-optimization-with-global-data-quantums-portfolio-optimizer)

---


## Running Tests

### Frontend (React)
```sh
npx jest
# or
npm test
```

### Python Backend
```sh
pytest backend/src/main/python/
# or
pytest tests/
```

### Java Backend
```sh
cd backend
mvn test
```

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
