# Quantum Financial Portfolio Optimization v0.0.1-alpha

🎉 **Welcome to the first alpha release of quantumFPO!** 

This release introduces a complete full-stack quantum-inspired portfolio optimization platform with modern microservices architecture.

## 🚀 What's New

### Complete Full-Stack Application
- **React Frontend** with modern Vite build system
- **Spring Boot Java Backend** with RESTful APIs
- **FastAPI Python Backend** with quantum optimization algorithms
- **Docker Containerization** for all services
- **CI/CD Pipeline** with comprehensive testing

### Quantum-Inspired Portfolio Optimization
- **Classical Optimization** using PyPortfolioOpt for efficient frontier calculation
- **Quantum-Inspired Hybrid** algorithms using Qiskit for enhanced optimization
- **Risk Management** with configurable VaR (Value at Risk) constraints
- **Real-time Health Monitoring** across all optimization engines

### Production-Ready Infrastructure
- **Multi-platform Docker Images** (AMD64/ARM64)
- **Container Orchestration** with Docker Compose
- **Security Scanning** with automated vulnerability detection
- **Performance Testing** with load testing capabilities
- **Health Check Integration** for production monitoring

## 📊 Technical Highlights

- **89 Python Tests** ensuring algorithm correctness
- **Multi-service Architecture** with proper API boundaries
- **Comprehensive CI/CD** with GitHub Actions
- **Security-First Approach** with container scanning
- **Development Tools** for easy local setup

## 🎯 Getting Started

### Quick Start with Docker
```bash
# Clone the repository
git clone https://github.com/lxtececo/quantumFPO.git
cd quantumFPO

# Start all services
docker compose up -d

# Access the application
# Frontend: http://localhost:3000
# Java API: http://localhost:8080
# Python API: http://localhost:8002
```

### Development Setup
```bash
# Use the container manager script
./scripts/container-manager.sh dev-start

# Or on Windows
.\scripts\container-manager.ps1 dev-start
```

## 🔗 Container Images

Pre-built images are available in GitHub Container Registry:
- `ghcr.io/lxtececo/quantumfpo-frontend:v0.0.1-alpha`
- `ghcr.io/lxtececo/quantumfpo-java-backend:v0.0.1-alpha`
- `ghcr.io/lxtececo/quantumfpo-python-backend:v0.0.1-alpha`

## 📋 Known Limitations

This is an **alpha release** with the following limitations:
- Uses simulated market data (real data integration planned)
- Basic UI without advanced visualizations
- No persistent database storage yet
- No user authentication system

## 🎯 What's Next?

**v0.0.2-alpha** will include:
- Real market data integration
- Enhanced UI with charts and portfolio visualizations
- Database persistence for portfolio history
- User authentication and portfolio management
- Extended quantum algorithms

## 🤝 Contributing

We welcome contributions! Please see our [development documentation](./reports/) for guidelines on:
- Setting up the development environment
- Running tests and quality checks
- Container management and deployment
- Architecture and design patterns

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/lxtececo/quantumFPO/issues)
- **Documentation**: [Project README](./README.md)
- **Reports**: [Development Reports](./reports/)

---

**Thank you for trying quantumFPO v0.0.1-alpha!** 🚀

Your feedback is invaluable as we continue developing this quantum-inspired portfolio optimization platform.