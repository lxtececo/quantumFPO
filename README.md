
# Quantum Financial Portfolio Optimization (quantumFPO)

[![Java CI](https://github.com/lxtececo/quantumFPO/actions/workflows/maven.yml/badge.svg)](https://github.com/lxtececo/quantumFPO/actions/workflows/maven.yml)
[![Node.js CI](https://github.com/lxtececo/quantumFPO/actions/workflows/node.js.yml/badge.svg)](https://github.com/lxtececo/quantumFPO/actions/workflows/node.js.yml)
[![Python Tests](https://github.com/lxtececo/quantumFPO/actions/workflows/python-tests.yml/badge.svg)](https://github.com/lxtececo/quantumFPO/actions/workflows/python-tests.yml)

## Project Overview
This project is a full-stack application for quantum-inspired financial portfolio optimization. It features a fast JavaScript frontend (React + Vite), a Spring Boot backend for RESTful services, and a Python microservice for advanced portfolio optimization using PyPortfolioOpt.

---

## Project Structure

This project follows a clean, organized structure with clear separation between frontend and backend components:

```
quantumFPO/
├── 📁 backend/                    # Java Spring Boot Backend
│   ├── pom.xml                   # Maven configuration
│   ├── 📁 src/main/java/         # Java source code
│   │   └── 📁 com/quantumfpo/    # Main application packages
│   │       ├── 📁 stocks/        # Stock-related services & controllers
│   │       │   ├── 📁 controller/ # REST API controllers
│   │       │   ├── 📁 model/      # Data models & DTOs
│   │       │   └── 📁 service/    # Business logic services
│   │       └── StocksApplication.java # Spring Boot main class
│   ├── 📁 src/main/python/       # Python optimization scripts
│   │   ├── classic_portfolio_opt.py   # Classical optimization
│   │   ├── hybrid_portfolio_opt.py    # Quantum-classical hybrid
│   │   └── qc_setup.py               # Quantum computing setup
│   └── 📁 src/test/              # Backend tests
│       ├── 📁 java/              # Java unit & integration tests
│       └── 📁 python/            # Python algorithm tests
├── 📁 frontend/                   # React Frontend Application
│   ├── 📁 src/                   # React source code
│   │   ├── App.jsx               # Main React component
│   │   ├── main.jsx              # Application entry point
│   │   └── 📁 assets/            # Static assets
│   ├── 📁 public/                # Public static files
│   ├── 📁 test/                  # Frontend tests (Jest)
│   ├── 📁 coverage/              # Test coverage reports
│   └── 📁 node_modules/          # Frontend dependencies
├── 📁 .venv/                     # Python virtual environment
├── 📁 .vscode/                   # VS Code workspace settings
├── 📁 .git/                      # Git version control
├── package.json                  # Node.js dependencies & scripts
├── package-lock.json             # Node.js dependency lock file
├── vite.config.js                # Vite build configuration
├── jest.config.js                # Test configuration
├── eslint.config.js              # Code linting rules
├── babel.config.js               # Babel transpilation
├── index.html                    # Main HTML template
├── README.md                     # Project documentation
└── TEST_COVERAGE_ENHANCEMENT_REPORT.md # Test coverage details
```

### Architecture Components

- **🚀 Frontend (React + Vite)**: Modern, fast frontend with hot reload, component testing, and responsive design
- **☕ Backend (Spring Boot)**: RESTful API server with dependency injection, auto-configuration, and comprehensive testing
- **🐍 Python Microservices**: Quantum and classical portfolio optimization algorithms with scientific computing libraries
- **🧪 Testing Suite**: Complete test coverage across all layers with unit, integration, and end-to-end testing
- **⚡ Development Tools**: Modern toolchain with Vite, Jest, ESLint, Maven, and Python virtual environments

---

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
# Run from root directory (package.json is now at root level)
npm test
# or with coverage
npm run test:coverage
```

### Python Backend
```sh
cd backend
python -m pytest src/test/python/ -v
# or for specific test files
python -m pytest src/test/python/test_hybrid_simplified.py -v
```

### Java Backend
```sh
# Run from backend directory (pom.xml is located in backend/)
cd backend
mvn test
```

### Java Backend Code Coverage Reports
Generate comprehensive test coverage reports using JaCoCo:

```sh
# Run tests with coverage collection
cd backend
mvn clean test

# Generate coverage reports (HTML, XML, CSV formats)
mvn jacoco:report

# Check coverage against thresholds (70% instruction, 65% branch)
mvn jacoco:check
```

**View Coverage Reports:**
- **Interactive HTML Report**: Open `backend/target/site/jacoco/index.html` in your browser
- **XML Report**: `backend/target/site/jacoco/jacoco.xml` (CI/CD integration)
- **CSV Report**: `backend/target/site/jacoco/jacoco.csv` (data analysis)

**Current Coverage:** ~59% instruction coverage with comprehensive error scenario testing

## 🚀 Continuous Integration & Deployment

The project includes comprehensive GitHub Actions workflows for automated testing:

### Available CI/CD Workflows

1. **🌐 Frontend Testing** (`node.js.yml`): React component tests with Jest
2. **☕ Java Backend Testing** (`maven.yml`): Spring Boot tests with JaCoCo coverage  
3. **🐍 Python Testing** (`python-tests.yml`): PyPortfolioOpt and quantum algorithm tests

### Python CI Features
- **Multi-version Testing**: Python 3.9, 3.10, 3.11
- **Dependency Caching**: Fast builds with pip cache
- **Coverage Reports**: pytest with coverage reporting
- **Integration Tests**: Standalone script execution validation
- **Quantum Dependencies**: Qiskit and quantum optimization libraries

### Triggering CI
Tests run automatically on:
- Push to `main` or `develop` branches
- Pull requests to `main` or `develop`
- Changes to relevant source files

### Local Testing Commands
```sh
# Python tests (matches CI exactly)
cd backend
python -m pytest src/test/python/ -v --cov=src/main/python

# Java tests with coverage
mvn clean test jacoco:report

# Frontend tests
npm test
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
# Run from root directory (package.json is now at root level)
npm install
```

### 3. Start the Frontend (React + Vite)
```sh
npm run dev
```
Frontend will run at [http://localhost:5173](http://localhost:5173).

### 4. Setup Python Environment
```sh
# Create virtual environment in project root
python -m venv .venv
# On Windows:
.venv\Scripts\activate
# On macOS/Linux:
source .venv/bin/activate

# Install Python dependencies
cd backend/src/main/python
pip install -r requirements.txt
# Or manually: pip install pypfopt pandas numpy scikit-learn qiskit pytest
```

### 5. Start the Spring Boot Backend
```sh
# Run from backend directory (pom.xml is located in backend/)
cd backend
mvn spring-boot:run
# Or use your IDE to run backend/src/main/java/.../StocksApplication.java
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

## Development Benefits

### Clean Architecture
- **🎯 Clear Separation**: Frontend and backend are completely separated for focused development
- **📦 Modular Design**: Each component can be developed, tested, and deployed independently  
- **🔧 Easy Maintenance**: Well-organized structure makes debugging and updates straightforward
- **👥 Team Collaboration**: Multiple developers can work on different parts without conflicts

### Professional Structure
- **📁 Industry Standard**: Follows established patterns used by major tech companies
- **🚀 Scalable**: Ready for microservices architecture and containerization
- **🔄 CI/CD Ready**: Structure supports automated testing and deployment pipelines
- **📚 Self-Documenting**: Clear folder hierarchy makes codebase exploration intuitive

### Development Experience
- **⚡ Fast Iteration**: Hot reload for frontend, auto-restart for backend changes
- **🧪 Comprehensive Testing**: Isolated test suites for each component
- **🛠️ Modern Tooling**: Latest versions of React, Spring Boot, and Python frameworks
- **📊 Monitoring**: Built-in logging, error tracking, and test coverage reporting

---

## License
MIT
