#!/bin/bash

# Startup script for Python Portfolio Optimization API
# This script starts the FastAPI server for portfolio optimization

echo "Starting Python Portfolio Optimization API..."

# Navigate to the Python source directory
cd "$(dirname "$0")"

# Check if virtual environment exists
if [ ! -d "../../../.venv" ]; then
    echo "Virtual environment not found. Please create one first:"
    echo "python -m venv .venv"
    echo "source .venv/bin/activate  # On Windows: .venv\\Scripts\\activate"
    echo "pip install -r requirements.txt"
    exit 1
fi

# Activate virtual environment (Linux/macOS)
source ../../../.venv/bin/activate

# Check if on Windows
if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" || "$OSTYPE" == "cygwin" ]]; then
    # Windows activation
    source ../../../.venv/Scripts/activate
fi

# Install/upgrade dependencies
echo "Installing/updating Python dependencies..."
pip install -r requirements.txt

# Start the FastAPI server
echo "Starting FastAPI server on http://localhost:8001..."
uvicorn portfolio_api:app --host 0.0.0.0 --port 8001 --reload --log-level info

echo "Python Portfolio Optimization API stopped."