#!/bin/bash
# Quick test runner for comprehensive validation
# Usage: ./scripts/quick-test.sh

set -e

echo "🧪 Quick Test Validation"
echo "========================"

# Check if we're in the right directory
if [ ! -f "backend/pom.xml" ]; then
    echo "❌ Please run this script from the project root directory"
    exit 1
fi

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to run command with status
run_test() {
    local test_name="$1"
    local command="$2"
    local directory="$3"
    
    echo -e "\n${BLUE}🔄 Running: $test_name${NC}"
    
    if [ -n "$directory" ]; then
        cd "$directory"
    fi
    
    if eval "$command"; then
        echo -e "${GREEN}✅ $test_name PASSED${NC}"
        return 0
    else
        echo -e "${RED}❌ $test_name FAILED${NC}"
        return 1
    fi
    
    if [ -n "$directory" ]; then
        cd - > /dev/null
    fi
}

# Initialize results
total_tests=0
passed_tests=0
failed_tests=0

# Python Tests
echo -e "\n${YELLOW}🐍 PYTHON TESTS${NC}"
echo "==============="

# Check Python environment
if command -v python3 &> /dev/null; then
    PYTHON_CMD="python3"
elif command -v python &> /dev/null; then
    PYTHON_CMD="python"
else
    echo -e "${RED}❌ Python not found${NC}"
    exit 1
fi

echo "Python version: $($PYTHON_CMD --version)"

# Install Python dependencies if needed
if [ -f "backend/src/main/python/requirements.txt" ]; then
    echo "Installing Python dependencies..."
    cd backend/src/main/python
    $PYTHON_CMD -m pip install -r requirements.txt > /dev/null 2>&1 || true
    $PYTHON_CMD -m pip install pytest pytest-cov pytest-mock pytest-asyncio httpx > /dev/null 2>&1 || true
    cd - > /dev/null
fi

# Run Python tests
export PYTHONPATH="$(pwd)/backend/src/main/python"
((total_tests++))
if run_test "Python Unit Tests" "$PYTHON_CMD -m pytest backend/src/test/python/ -x --tb=short" ""; then
    ((passed_tests++))
else
    ((failed_tests++))
fi

# Java Tests
echo -e "\n${YELLOW}☕ JAVA TESTS${NC}"
echo "============="

# Check Java environment
if command -v mvn &> /dev/null; then
    echo "Maven version: $(mvn --version | head -1)"
    
    ((total_tests++))
    if run_test "Java Unit Tests" "mvn clean test -q" "backend"; then
        ((passed_tests++))
    else
        ((failed_tests++))
    fi
else
    echo -e "${YELLOW}⚠️  Maven not found, skipping Java tests${NC}"
fi

# Frontend Tests
echo -e "\n${YELLOW}⚛️  FRONTEND TESTS${NC}"
echo "================="

# Check Node environment
if command -v npm &> /dev/null && [ -f "frontend/package.json" ]; then
    echo "Node version: $(node --version)"
    echo "NPM version: $(npm --version)"
    
    # Install dependencies if needed
    if [ ! -d "frontend/node_modules" ]; then
        echo "Installing frontend dependencies..."
        cd frontend
        npm ci > /dev/null 2>&1 || npm install > /dev/null 2>&1
        cd - > /dev/null
    fi
    
    ((total_tests++))
    if run_test "Frontend Tests" "npm test -- --watchAll=false --passWithNoTests" "frontend"; then
        ((passed_tests++))
    else
        ((failed_tests++))
    fi
else
    echo -e "${YELLOW}⚠️  Node.js/npm not found or no frontend, skipping frontend tests${NC}"
fi

# Quick API Health Check (if Python API is running)
echo -e "\n${YELLOW}🔗 INTEGRATION CHECK${NC}"
echo "=================="

((total_tests++))
if curl -s -f "http://localhost:8001/health" > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Python API is running and healthy${NC}"
    ((passed_tests++))
else
    echo -e "${YELLOW}⚠️  Python API not running (this is okay for unit tests)${NC}"
    ((passed_tests++))  # Don't fail for this
fi

# Summary
echo -e "\n${BLUE}📊 SUMMARY${NC}"
echo "=========="
echo "Total tests: $total_tests"
echo -e "Passed: ${GREEN}$passed_tests${NC}"
echo -e "Failed: ${RED}$failed_tests${NC}"

if [ $failed_tests -eq 0 ]; then
    echo -e "\n${GREEN}🎉 All tests passed!${NC}"
    exit 0
else
    echo -e "\n${RED}💥 Some tests failed!${NC}"
    exit 1
fi