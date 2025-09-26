
# Quantum Financial Portfolio Optimization (quantumFPO)

[![Containerized CI/CD](https://github.com/lxtececo/quantumFPO/actions/workflows/containerized-ci-cd.yml/badge.svg)](https://github.com/lxtececo/quantumFPO/actions/workflows/containerized-ci-cd.yml)
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
│   │   ├── portfolio_api.py           # FastAPI REST service
│   │   └── requirements.txt           # Python dependencies
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
│   └── package.json              # Frontend dependencies
├── 📁 reports/                   # 📊 Development & Testing Reports
│   ├── BACKEND_ARCHITECTURE_ENHANCEMENT_REPORT.md
│   ├── BACKEND_TEST_ENHANCEMENT_REPORT.md  
│   ├── COMPREHENSIVE_TESTING_STRATEGY.md
│   ├── FINAL_COVERAGE_REPORT.md
│   ├── GITHUB_ACTIONS_FIX_REPORT.md
│   ├── GITHUB_WORKFLOW_FIX_REPORT.md
│   ├── INTEGRATION_E2E_TEST_AUTOMATION_REPORT.md
│   ├── JAVA_BACKEND_COVERAGE_REPORT.md
│   ├── JAVA_TEST_FIX_REPORT.md
│   ├── PYTHON_CI_IMPLEMENTATION_REPORT.md
│   ├── PYTHON_TEST_DEPENDENCY_FIX_REPORT.md
│   └── TEST_COVERAGE_ENHANCEMENT_REPORT.md
├── 📁 scripts/                   # Build & utility scripts
│   ├── quick-test.sh             # Cross-platform testing script
│   ├── run-all-tests.ps1         # PowerShell test runner
│   ├── container-manager.sh      # Container management (Linux/macOS)
│   └── container-manager.ps1     # Container management (Windows)
├── 📁 .github/workflows/         # CI/CD pipelines
│   └── containerized-ci-cd.yml   # Docker-based CI/CD pipeline
├── 🐳 docker-compose.yml          # Production container orchestration
├── 🐳 docker-compose.dev.yml      # Development container orchestration
├── 🐳 CONTAINERIZATION_COMPLETE.md # Complete containerization guide
├── 🐳 CONTAINERIZATION_SUMMARY.md  # Containerization summary
├── 📁 .venv/                     # Python virtual environment
├── 📁 .vscode/                   # VS Code workspace settings
├── 📁 .git/                      # Git version control
└── README.md                     # 📖 Project documentation
```

### Architecture Components

- **🚀 Frontend (React + Vite)**: Modern, fast frontend with hot reload, component testing, and responsive design
- **☕ Backend (Spring Boot)**: RESTful API server with dependency injection, auto-configuration, and comprehensive testing
- **🐍 Python FastAPI Service**: High-performance REST API for quantum and classical portfolio optimization with comprehensive logging
- **🐳 Containerization**: Complete Docker setup with multi-stage builds, development/production environments, and container orchestration
- **🧪 Testing Suite**: Complete test coverage across all layers with unit, integration, and end-to-end testing
- **⚡ Development Tools**: Modern toolchain with Vite, Jest, ESLint, Maven, and Python virtual environments
- **🚀 CI/CD Pipelines**: Automated testing, building, security scanning, and deployment with both standard and containerized workflows
- **📊 Documentation**: Comprehensive development reports and testing documentation

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


---

## 📊 Development Reports

The `reports/` folder contains detailed documentation of development processes, testing strategies, and implementation decisions:

### Testing & Quality Assurance
- **[Comprehensive Testing Strategy](reports/COMPREHENSIVE_TESTING_STRATEGY.md)**: Overall testing approach and methodologies
- **[Final Coverage Report](reports/FINAL_COVERAGE_REPORT.md)**: Complete test coverage analysis across all components
- **[Test Coverage Enhancement Report](reports/TEST_COVERAGE_ENHANCEMENT_REPORT.md)**: Detailed coverage improvements and metrics

### Backend Development
- **[Backend Architecture Enhancement](reports/BACKEND_ARCHITECTURE_ENHANCEMENT_REPORT.md)**: Spring Boot architecture improvements
- **[Backend Test Enhancement](reports/BACKEND_TEST_ENHANCEMENT_REPORT.md)**: Java backend testing enhancements
- **[Java Backend Coverage Report](reports/JAVA_BACKEND_COVERAGE_REPORT.md)**: JUnit and integration test coverage
- **[Java Test Fix Report](reports/JAVA_TEST_FIX_REPORT.md)**: Java testing framework fixes and improvements

### Python Development
- **[Python CI Implementation Report](reports/PYTHON_CI_IMPLEMENTATION_REPORT.md)**: Python continuous integration setup
- **[Python Test Dependency Fix](reports/PYTHON_TEST_DEPENDENCY_FIX_REPORT.md)**: Python testing environment fixes

### CI/CD & DevOps
- **[GitHub Actions Fix Report](reports/GITHUB_ACTIONS_FIX_REPORT.md)**: GitHub Actions workflow improvements
- **[GitHub Workflow Fix Report](reports/GITHUB_WORKFLOW_FIX_REPORT.md)**: CI/CD pipeline enhancements
- **[Integration E2E Test Automation](reports/INTEGRATION_E2E_TEST_AUTOMATION_REPORT.md)**: End-to-end testing automation

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

The project includes comprehensive GitHub Actions workflows for automated testing and deployment:

### 🚀 Primary CI/CD Pipeline

**🐳 Containerized CI/CD** (`containerized-ci-cd.yml`): Modern Docker-based pipeline with:
- **Multi-service builds** with parallel execution and caching
- **Security scanning** with Trivy vulnerability detection
- **Integration testing** with Docker Compose orchestration
- **Multi-architecture support** (amd64/arm64)
- **Performance testing** and deployment automation
- **Staged deployment** (staging → production with approvals)

### 📊 Individual Service Workflows

1. **🌐 Frontend Testing** (`node.js.yml`): React component tests with Jest
2. **☕ Java Backend Testing** (`maven.yml`): Spring Boot tests with JaCoCo coverage  
3. **🐍 Python Testing** (`python-tests.yml`): PyPortfolioOpt and quantum algorithm tests

### 🔄 Pipeline Features
- **Python 3.11+ Testing**: Modern Python version compatibility
- **Docker Layer Caching**: Fast builds with optimized caching
- **Coverage Reports**: Comprehensive test coverage across all services
- **Security Scanning**: Automated vulnerability detection
- **Container Registry**: Automated image builds and publishing

### Triggering CI
Tests and deployments run automatically on:
- Push to `main` or `develop` branches
- Pull requests to `main` or `develop`
- Changes to relevant source files or Docker configurations

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

## 🚀 Quick Setup Instructions

### 🐳 Docker Setup (Recommended)

**Prerequisites:** Docker Desktop (Windows/macOS) or Docker Engine (Linux)

```bash
# Clone the repository
git clone https://github.com/lxtececo/quantumFPO.git
cd quantumFPO

# Start development environment (Linux/macOS)
./scripts/container-manager.sh dev-start

# Start development environment (Windows)
.\scripts\container-manager.ps1 dev-start

# Or use Docker Compose directly
docker-compose -f docker-compose.dev.yml up -d
```

**Service URLs:**
- Frontend: http://localhost:5173
- Java API: http://localhost:8080
- Python API: http://localhost:8002

📖 **See [CONTAINERIZATION_COMPLETE.md](./CONTAINERIZATION_COMPLETE.md) for the complete Docker setup guide**

### 📦 Manual Setup (Traditional)

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

### 4. Setup Python Environment & Start FastAPI Service
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
# Or manually: pip install pypfopt pandas numpy scikit-learn qiskit pytest fastapi uvicorn

# Start the Python FastAPI service (runs on port 8002)
python -m uvicorn portfolio_api:app --host 0.0.0.0 --port 8002 --reload
```
Python FastAPI service will run at [http://localhost:8002](http://localhost:8002).

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
