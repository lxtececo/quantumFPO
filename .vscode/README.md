# VS Code Configuration for quantumFPO

This directory contains VS Code configuration files to help with development and debugging of the quantumFPO application.

## Launch Configurations

### Python FastAPI Configurations

1. **Python: FastAPI Portfolio API**
   - Launches the FastAPI server directly using the Python script
   - Best for basic testing and development
   - Uses the project's virtual environment (`.venv`)

2. **Python: FastAPI Portfolio API (Debug)**
   - Launches the FastAPI server with debugging enabled
   - Allows setting breakpoints in your Python code
   - Useful for troubleshooting portfolio optimization logic

3. **Python: Uvicorn FastAPI Server**
   - Launches the FastAPI server using uvicorn module
   - Includes hot-reload for development
   - Recommended for active development with automatic restarts

### Java Spring Boot Configuration

4. **Spring Boot-StocksApplication<stocks-backend>**
   - Launches the main Java Spring Boot application
   - Connects to the Python FastAPI service via REST calls
   - Uses environment variables from `.env` file

### Compound Configurations

5. **Launch Full Backend Stack**
   - Starts both Python FastAPI server and Java Spring Boot application
   - Recommended for full-stack testing
   - Automatically manages both services

6. **Launch Full Stack (Backend + Python Debug)**
   - Starts Python FastAPI in debug mode + Java Spring Boot
   - Best for debugging issues in the Python optimization code
   - Allows breakpoints in both services

### Jest Testing Configurations

7. **Jest: Run All Tests** - Runs all frontend tests
8. **Jest: Watch Mode** - Runs tests in watch mode
9. **Jest: Debug Current Test** - Debug specific test file

## Tasks

The `tasks.json` file includes helpful tasks accessible via `Ctrl+Shift+P` → `Tasks: Run Task`:

- **Start Python FastAPI Server** - Start the API server as a background task
- **Install Python Dependencies** - Install/update Python packages from requirements.txt
- **Test Python API Health** - Quick health check of the running API
- **Run Python Tests** - Execute Python test suite
- **Stop Python FastAPI Server** - Stop any running Python processes

## Settings

The `settings.json` file configures:
- Python interpreter to use the project's virtual environment
- Python path to include the backend Python modules
- Testing configuration for both Python (pytest) and JavaScript (Jest)
- File associations and analysis paths

## Usage

1. **Start Development**: Use "Launch Full Backend Stack" to start both services
2. **Debug Python**: Use "Launch Full Stack (Backend + Python Debug)" to debug Python code
3. **Debug Java**: Use "Spring Boot-StocksApplication" + "Python: Uvicorn FastAPI Server" separately
4. **Testing**: Use the respective Jest and pytest configurations

## Port Configuration

- Java Spring Boot: http://localhost:8080
- Python FastAPI: http://localhost:8001
- Frontend (when running): http://localhost:5173

## Environment Variables

Make sure you have a `.env` file in the workspace root with any necessary environment variables for the Java application.