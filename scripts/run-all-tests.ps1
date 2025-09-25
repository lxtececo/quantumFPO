# PowerShell script for comprehensive local testing
# Usage: .\scripts\run-all-tests.ps1

param(
    [string]$TestType = "all",  # all, python, java, frontend, integration
    [switch]$Coverage = $false,
    [switch]$Verbose = $false
)

Write-Host "🧪 Starting Comprehensive Test Suite" -ForegroundColor Green
Write-Host "Test Type: $TestType" -ForegroundColor Yellow
Write-Host "Coverage: $Coverage" -ForegroundColor Yellow
Write-Host "===========================================" -ForegroundColor Green

$ErrorActionPreference = "Continue"
$results = @{}

# Helper function to run command and capture result
function Invoke-TestCommand {
    param(
        [string]$Name,
        [string]$Command,
        [string]$WorkingDirectory = "."
    )
    
    Write-Host "`n🔄 Running: $Name" -ForegroundColor Cyan
    Write-Host "Command: $Command" -ForegroundColor Gray
    Write-Host "Working Directory: $WorkingDirectory" -ForegroundColor Gray
    
    try {
        Push-Location $WorkingDirectory
        $startTime = Get-Date
        
        if ($Verbose) {
            Invoke-Expression $Command
            $exitCode = $LASTEXITCODE
        } else {
            $output = Invoke-Expression $Command 2>&1
            $exitCode = $LASTEXITCODE
            if ($exitCode -ne 0) {
                Write-Host $output -ForegroundColor Red
            } else {
                Write-Host "✅ Success" -ForegroundColor Green
            }
        }
        
        $duration = (Get-Date) - $startTime
        $results[$Name] = @{
            ExitCode = $exitCode
            Duration = $duration
            Status = if ($exitCode -eq 0) { "PASS" } else { "FAIL" }
        }
        
        Write-Host "Duration: $($duration.TotalSeconds) seconds" -ForegroundColor Gray
        
    } catch {
        Write-Host "❌ Error: $($_.Exception.Message)" -ForegroundColor Red
        $results[$Name] = @{
            ExitCode = 1
            Duration = (Get-Date) - $startTime
            Status = "ERROR"
        }
    } finally {
        Pop-Location
    }
}

# Python Tests
if ($TestType -eq "all" -or $TestType -eq "python") {
    Write-Host "`n🐍 PYTHON TESTS" -ForegroundColor Magenta
    Write-Host "===============" -ForegroundColor Magenta
    
    # Check Python environment
    Invoke-TestCommand -Name "Python Version Check" -Command "python --version"
    
    # Install Python dependencies
    Invoke-TestCommand -Name "Python Dependencies" -Command "pip install -r requirements.txt" -WorkingDirectory "backend\src\main\python"
    Invoke-TestCommand -Name "Python Test Dependencies" -Command "pip install pytest pytest-cov pytest-mock pytest-asyncio httpx" -WorkingDirectory "backend\src\main\python"
    
    # Lint Python code
    Invoke-TestCommand -Name "Python Lint (flake8)" -Command "pip install flake8 && flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics" -WorkingDirectory "backend\src\main\python"
    
    # Run Python unit tests
    $pythonTestCommand = if ($Coverage) { 
        "python -m pytest src\test\python\ --cov=src\main\python --cov-report=term-missing --cov-report=xml --cov-report=html -v"
    } else {
        "python -m pytest src\test\python\ -v"
    }
    
    $env:PYTHONPATH = "$PWD\backend\src\main\python"
    Invoke-TestCommand -Name "Python Unit Tests" -Command $pythonTestCommand -WorkingDirectory "backend"
}

# Java Tests  
if ($TestType -eq "all" -or $TestType -eq "java") {
    Write-Host "`n☕ JAVA TESTS" -ForegroundColor Magenta
    Write-Host "=============" -ForegroundColor Magenta
    
    # Check Java environment
    Invoke-TestCommand -Name "Java Version Check" -Command "java -version"
    Invoke-TestCommand -Name "Maven Version Check" -Command "mvn -version"
    
    # Run Java tests
    $javaTestCommand = if ($Coverage) {
        "mvn clean test jacoco:report"
    } else {
        "mvn clean test"
    }
    
    Invoke-TestCommand -Name "Java Unit Tests" -Command $javaTestCommand -WorkingDirectory "backend"
    
    # Generate test reports
    Invoke-TestCommand -Name "Java Test Reports" -Command "mvn surefire-report:report-only" -WorkingDirectory "backend"
}

# Frontend Tests
if ($TestType -eq "all" -or $TestType -eq "frontend") {
    Write-Host "`n⚛️  FRONTEND TESTS" -ForegroundColor Magenta
    Write-Host "=================" -ForegroundColor Magenta
    
    # Check Node environment
    Invoke-TestCommand -Name "Node Version Check" -Command "node --version"
    Invoke-TestCommand -Name "NPM Version Check" -Command "npm --version"
    
    # Install frontend dependencies
    Invoke-TestCommand -Name "Frontend Dependencies" -Command "npm ci" -WorkingDirectory "frontend"
    
    # Lint frontend code
    Invoke-TestCommand -Name "Frontend Lint" -Command "npm run lint" -WorkingDirectory "frontend"
    
    # Run frontend tests
    $frontendTestCommand = if ($Coverage) {
        "npm test -- --coverage --watchAll=false"
    } else {
        "npm test -- --watchAll=false"
    }
    
    Invoke-TestCommand -Name "Frontend Tests" -Command $frontendTestCommand -WorkingDirectory "frontend"
    
    # Build frontend
    Invoke-TestCommand -Name "Frontend Build" -Command "npm run build" -WorkingDirectory "frontend"
}

# Integration Tests
if ($TestType -eq "all" -or $TestType -eq "integration") {
    Write-Host "`n🔗 INTEGRATION TESTS" -ForegroundColor Magenta
    Write-Host "===================" -ForegroundColor Magenta
    
    # Start Python API in background
    Write-Host "🚀 Starting Python FastAPI server..." -ForegroundColor Cyan
    $env:PYTHONPATH = "$PWD\backend\src\main\python"
    
    Push-Location "backend\src\main\python"
    $pythonProcess = Start-Process -FilePath "python" -ArgumentList "portfolio_api.py" -PassThru -WindowStyle Hidden
    Pop-Location
    
    # Wait for API to start
    Write-Host "⏳ Waiting for API to start..." -ForegroundColor Yellow
    Start-Sleep -Seconds 10
    
    try {
        # Test API health
        Invoke-TestCommand -Name "API Health Check" -Command "curl -f http://localhost:8001/health"
        
        # Run integration tests
        $env:PYTHONPATH = "$PWD\backend\src\main\python"
        Invoke-TestCommand -Name "Integration Tests" -Command "python -m pytest src\test\python\test_integration_e2e.py -v -m `"integration and not slow`"" -WorkingDirectory "backend"
        
    } finally {
        # Stop Python API
        if ($pythonProcess -and !$pythonProcess.HasExited) {
            Write-Host "🛑 Stopping Python API server..." -ForegroundColor Yellow
            Stop-Process -Id $pythonProcess.Id -Force -ErrorAction SilentlyContinue
        }
        
        # Kill any remaining python processes
        Get-Process -Name "python" -ErrorAction SilentlyContinue | Where-Object { $_.CommandLine -like "*portfolio_api*" } | Stop-Process -Force -ErrorAction SilentlyContinue
    }
}

# Summary Report
Write-Host "`n📊 TEST RESULTS SUMMARY" -ForegroundColor Green
Write-Host "=======================" -ForegroundColor Green

$totalTests = $results.Count
$passedTests = ($results.Values | Where-Object { $_.Status -eq "PASS" }).Count
$failedTests = ($results.Values | Where-Object { $_.Status -eq "FAIL" }).Count
$errorTests = ($results.Values | Where-Object { $_.Status -eq "ERROR" }).Count

Write-Host "Total Tests: $totalTests" -ForegroundColor White
Write-Host "Passed: $passedTests" -ForegroundColor Green
Write-Host "Failed: $failedTests" -ForegroundColor Red
Write-Host "Errors: $errorTests" -ForegroundColor Yellow

Write-Host "`nDetailed Results:" -ForegroundColor White
foreach ($test in $results.GetEnumerator() | Sort-Object Name) {
    $status = $test.Value.Status
    $duration = [math]::Round($test.Value.Duration.TotalSeconds, 2)
    
    $color = switch ($status) {
        "PASS" { "Green" }
        "FAIL" { "Red" }
        "ERROR" { "Yellow" }
    }
    
    Write-Host "  $($status.PadRight(5)) | $($duration.ToString().PadLeft(6))s | $($test.Name)" -ForegroundColor $color
}

# Coverage Reports
if ($Coverage) {
    Write-Host "`n📈 COVERAGE REPORTS" -ForegroundColor Green
    Write-Host "===================" -ForegroundColor Green
    
    if (Test-Path "backend\htmlcov\index.html") {
        Write-Host "Python Coverage: backend\htmlcov\index.html" -ForegroundColor Cyan
    }
    
    if (Test-Path "backend\target\site\jacoco\index.html") {
        Write-Host "Java Coverage: backend\target\site\jacoco\index.html" -ForegroundColor Cyan
    }
    
    if (Test-Path "frontend\coverage\lcov-report\index.html") {
        Write-Host "Frontend Coverage: frontend\coverage\lcov-report\index.html" -ForegroundColor Cyan
    }
}

# Exit with appropriate code
if ($failedTests -gt 0 -or $errorTests -gt 0) {
    Write-Host "`n❌ Some tests failed!" -ForegroundColor Red
    exit 1
} else {
    Write-Host "`n✅ All tests passed!" -ForegroundColor Green
    exit 0
}