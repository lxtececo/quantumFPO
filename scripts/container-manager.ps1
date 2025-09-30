# Container Build and Management Scripts for QuantumFPO
# PowerShell version for Windows
# Usage: .\scripts\container-manager.ps1 [command]

param(
    [Parameter(Position=0)]
    [string]$Command = "help",
    [Parameter(Position=1)]
    [string]$Service = "all",
    [string]$Version = "latest",
    [string]$Registry = "ghcr.io/lxtececo"
)

# Configuration
$ProjectName = "quantumfpo"
$Services = @("frontend", "java-backend", "python-backend")

# Helper functions
function Write-Log {
    param([string]$Message)
    Write-Host "[INFO] $Message" -ForegroundColor Blue
}

function Write-Warn {
    param([string]$Message)
    Write-Host "[WARN] $Message" -ForegroundColor Yellow
}

function Write-Error {
    param([string]$Message)
    Write-Host "[ERROR] $Message" -ForegroundColor Red
}

function Write-Success {
    param([string]$Message)
    Write-Host "[SUCCESS] $Message" -ForegroundColor Green
}

# Build individual service
function Build-Service {
    param([string]$ServiceName, [string]$Tag = $Version)
    
    Write-Log "Building $ServiceName..."
    
    switch ($ServiceName) {
        "frontend" {
            docker build -t "${ProjectName}-${ServiceName}:${Tag}" -f frontend/Dockerfile frontend/
        }
        "java-backend" {
            docker build -t "${ProjectName}-${ServiceName}:${Tag}" -f backend/Dockerfile backend/
        }
        "python-backend" {
            docker build -t "${ProjectName}-${ServiceName}:${Tag}" -f backend/src/main/python/Dockerfile .
        }
        default {
            Write-Error "Unknown service: $ServiceName"
            return $false
        }
    }
    
    if ($LASTEXITCODE -eq 0) {
        Write-Success "Built $ServiceName successfully"
        return $true
    } else {
        Write-Error "Failed to build $ServiceName"
        return $false
    }
}

# Build all services
function Build-All {
    Write-Log "Building all services..."
    $success = $true
    
    foreach ($service in $Services) {
        if (-not (Build-Service $service)) {
            $success = $false
        }
    }
    
    if ($success) {
        Write-Success "All services built successfully"
    } else {
        Write-Error "Some services failed to build"
    }
}

# Test individual service using development environment
function Test-Service {
    param([string]$ServiceName)
    
    $port = switch ($ServiceName) {
        "frontend" { 5173 }  # Development port
        "java-backend" { 8080 }
        "python-backend" { 8002 }
        default { 
            Write-Error "Unknown service: $ServiceName"
            return $false
        }
    }
    
    $healthEndpoint = switch ($ServiceName) {
        "frontend" { "/" }  # Frontend doesn't have dedicated health endpoint in dev
        "java-backend" { "/actuator/health" }
        "python-backend" { "/health" }
    }
    
    Write-Log "Testing $ServiceName using development environment..."
    
    # Check if development environment is running
    $runningContainers = docker ps --filter "name=quantumfpo-$ServiceName-dev" --format "{{.Names}}"
    
    if (-not $runningContainers) {
        Write-Log "Starting development environment for testing..."
        docker-compose -f docker-compose.dev.yml up -d $ServiceName
        
        if ($LASTEXITCODE -ne 0) {
            Write-Error "Failed to start development container for $ServiceName"
            return $false
        }
        
        # Wait for container to be ready
        Write-Log "Waiting for $ServiceName to be ready..."
        Start-Sleep -Seconds 20
    } else {
        Write-Log "Using existing development container for $ServiceName"
    }
    
    # Test health endpoint
    try {
        if ($ServiceName -eq "frontend") {
            # For frontend, just check if the server responds
            $response = Invoke-WebRequest -Uri "http://localhost:${port}" -TimeoutSec 10
            if ($response.StatusCode -eq 200) {
                Write-Success "$ServiceName is healthy (frontend serving)"
                $success = $true
            } else {
                Write-Error "$ServiceName health check failed with status $($response.StatusCode)"
                $success = $false
            }
        } else {
            $response = Invoke-WebRequest -Uri "http://localhost:${port}${healthEndpoint}" -TimeoutSec 10
            if ($response.StatusCode -eq 200) {
                Write-Success "$ServiceName is healthy"
                $success = $true
            } else {
                Write-Error "$ServiceName health check failed with status $($response.StatusCode)"
                $success = $false
            }
        }
    }
    catch {
        Write-Error "$ServiceName health check failed: $($_.Exception.Message)"
        docker logs "quantumfpo-$ServiceName-dev" 2>$null
        $success = $false
    }
    
    return $success
}

# Test all services using development environment
function Test-All {
    Write-Log "Testing all services using development environment..."
    
    # Start development environment
    Write-Log "Ensuring development environment is running..."
    docker-compose -f docker-compose.dev.yml up -d
    
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Failed to start development environment"
        return
    }
    
    # Wait for all services to be ready
    Write-Log "Waiting for all services to be ready..."
    Start-Sleep -Seconds 30
    
    $success = $true
    
    foreach ($service in $Services) {
        if (-not (Test-Service $service)) {
            $success = $false
        }
    }
    
    if ($success) {
        Write-Success "All service tests passed in development environment"
    } else {
        Write-Error "Some service tests failed in development environment"
        Write-Log "Check logs with: docker-compose -f docker-compose.dev.yml logs"
    }
}

# Start development environment
function Start-Development {
    Write-Log "Starting development environment..."
    docker-compose -f docker-compose.dev.yml up -d

    if ($LASTEXITCODE -ne 0) {
        Write-Error "Failed to start development environment"
        return
    }    Write-Log "Waiting for services to be ready..."
    Start-Sleep -Seconds 35
    
    Write-Log "Checking service health..."
    $healthyServices = 0
    
    try { 
        Invoke-WebRequest -Uri "http://localhost:5173" -TimeoutSec 5 | Out-Null
        Write-Success "Frontend dev server is ready"
        $healthyServices++
    } catch { 
        Write-Warn "Frontend dev server might still be starting" 
    }
    
    try { 
        Invoke-WebRequest -Uri "http://localhost:8080/actuator/health" -TimeoutSec 5 | Out-Null
        Write-Success "Java backend is ready"
        $healthyServices++
    } catch { 
        Write-Warn "Java backend might still be starting" 
    }
    
    try { 
        Invoke-WebRequest -Uri "http://localhost:8002/health" -TimeoutSec 5 | Out-Null
        Write-Success "Python backend is ready"
        $healthyServices++
    } catch { 
        Write-Warn "Python backend might still be starting" 
    }
    
    Write-Success "Development environment started ($healthyServices/3 services ready)"
    Write-Log "Frontend: http://localhost:5173 (Vite dev server with hot reload)"
    Write-Log "Java API: http://localhost:8080 (Spring Boot with dev profile)"
    Write-Log "Python API: http://localhost:8002 (FastAPI with auto-reload)"
    
    if ($healthyServices -lt 3) {
        Write-Warn "Some services may still be starting up. Wait a moment and check logs if needed."
        Write-Log "Check logs with: docker-compose -f docker-compose.dev.yml logs [service-name]"
    }
}

# Stop development environment
function Stop-Development {
    Write-Log "Stopping development environment..."
    docker-compose -f docker-compose.dev.yml down --remove-orphans
    
    if ($LASTEXITCODE -eq 0) {
        Write-Success "Development environment stopped"
    } else {
        Write-Error "Failed to stop development environment cleanly"
    }
}

# Start production environment
function Start-Production {
    Write-Log "Starting production environment..."
    docker-compose up -d
    
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Failed to start production environment"
        return
    }
    
    Write-Log "Waiting for services to be ready..."
    Start-Sleep -Seconds 45
    
    Write-Log "Checking service health..."
    try {
        Invoke-WebRequest -Uri "http://localhost:3000/health" -TimeoutSec 10 | Out-Null
        Invoke-WebRequest -Uri "http://localhost:8080/actuator/health" -TimeoutSec 10 | Out-Null
        Invoke-WebRequest -Uri "http://localhost:8002/health" -TimeoutSec 10 | Out-Null
        
        Write-Success "Production environment started"
        Write-Log "Frontend: http://localhost:3000"
        Write-Log "Java API: http://localhost:8080"
        Write-Log "Python API: http://localhost:8002"
    }
    catch {
        Write-Error "Health check failed: $($_.Exception.Message)"
        Write-Log "Check service logs with: docker-compose logs"
    }
}

# Stop production environment
function Stop-Production {
    Write-Log "Stopping production environment..."
    docker-compose down
    Write-Success "Production environment stopped"
}

# Push images to registry
function Push-Images {
    Write-Log "Pushing images to registry..."
    
    foreach ($service in $Services) {
        $localTag = "${ProjectName}-${service}:${Version}"
        $remoteTag = "${Registry}/${ProjectName}-${service}:${Version}"
        
        Write-Log "Tagging $service for registry..."
        docker tag $localTag $remoteTag
        
        Write-Log "Pushing $service to registry..."
        docker push $remoteTag
        
        if ($LASTEXITCODE -eq 0) {
            Write-Success "Pushed $service to registry"
        } else {
            Write-Error "Failed to push $service to registry"
        }
    }
}

# Pull images from registry
function Pull-Images {
    Write-Log "Pulling images from registry..."
    
    foreach ($service in $Services) {
        $remoteTag = "${Registry}/${ProjectName}-${service}:${Version}"
        
        Write-Log "Pulling $service from registry..."
        docker pull $remoteTag
        
        if ($LASTEXITCODE -eq 0) {
            # Tag as local image
            docker tag $remoteTag "${ProjectName}-${service}:${Version}"
            Write-Success "Pulled $service from registry"
        } else {
            Write-Error "Failed to pull $service from registry"
        }
    }
}

# Clean up containers and images
function Invoke-Cleanup {
    Write-Log "Cleaning up containers and images..."
    
    # Stop and remove all project containers
    $containers = docker ps -a --filter "name=$ProjectName" --format "{{.Names}}"
    if ($containers) {
        docker stop $containers | Out-Null
        docker rm $containers | Out-Null
    }
    
    # Remove project images
    $images = docker images --filter "reference=${ProjectName}-*" --format "{{.Repository}}:{{.Tag}}"
    if ($images) {
        docker rmi $images | Out-Null
    }
    
    # Clean up unused resources
    docker system prune -f | Out-Null
    
    Write-Success "Cleanup completed"
}

# Integration test using development environment
function Invoke-IntegrationTest {
    Write-Log "Running integration tests using development environment..."
    
    # Start development services
    Write-Log "Starting development environment for integration tests..."
    docker-compose -f docker-compose.dev.yml up -d

    if ($LASTEXITCODE -ne 0) {
        Write-Error "Failed to start development services for integration test"
        return
    }    # Wait for services to be fully ready
    Write-Log "Waiting for services to be ready..."
    Start-Sleep -Seconds 45
    
    # Check service health before running tests
    Write-Log "Checking service health before integration tests..."
    $healthyServices = 0
    
    try { 
        Invoke-WebRequest -Uri "http://localhost:5173" -TimeoutSec 5 | Out-Null
        Write-Log "Frontend dev server is ready"
        $healthyServices++
    } catch { 
        Write-Warn "Frontend dev server not responding" 
    }
    
    try { 
        Invoke-WebRequest -Uri "http://localhost:8080/actuator/health" -TimeoutSec 5 | Out-Null
        Write-Log "Java backend is ready"
        $healthyServices++
    } catch { 
        Write-Warn "Java backend not responding" 
    }
    
    try { 
        Invoke-WebRequest -Uri "http://localhost:8002/health" -TimeoutSec 5 | Out-Null
        Write-Log "Python backend is ready"
        $healthyServices++
    } catch { 
        Write-Warn "Python backend not responding" 
    }
    
    if ($healthyServices -lt 3) {
        Write-Warn "Not all services are healthy. Proceeding with available services..."
    }
    
    # Run integration tests
    Push-Location backend
    try {
        Write-Log "Running Python integration tests..."
        
        # Run Python backend tests
        docker exec quantumfpo-python-backend-dev python -m pytest src/test/python/test_integration_e2e.py -v -m "integration" 2>$null
        $pythonTestResult = $LASTEXITCODE
        
        # If container exec fails, try running tests from host with proper environment
        if ($pythonTestResult -ne 0) {
            Write-Log "Container exec failed, trying host-based test execution..."
            
            # Set environment variables for test
            $env:PYTHON_API_URL = "http://localhost:8002"
            $env:JAVA_API_URL = "http://localhost:8080"
            $env:FRONTEND_URL = "http://localhost:5173"
            
            python -m pytest src/test/python/test_integration_e2e.py -v -m "integration" --tb=short
            $pythonTestResult = $LASTEXITCODE
        }
        
        if ($pythonTestResult -eq 0) {
            Write-Success "Integration tests passed"
        } else {
            Write-Error "Integration tests failed"
            Write-Log "Showing recent container logs..."
            docker-compose -f docker-compose.dev.yml logs --tail=50
        }
    }
    catch {
        Write-Error "Failed to run integration tests: $($_.Exception.Message)"
        docker-compose -f docker-compose.dev.yml logs --tail=20
    }
    finally {
        Pop-Location
        Write-Log "Integration test completed. Development environment is still running."
        Write-Log "Use 'dev-stop' command to stop the development environment if needed."
    }
}

# Show usage
function Show-Usage {
    Write-Host "Container Management Script for QuantumFPO" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Usage: .\scripts\container-manager.ps1 [command] [options]" -ForegroundColor White
    Write-Host ""
    Write-Host "Commands:" -ForegroundColor Yellow
    Write-Host "  build [service]     Build service(s) (frontend|java-backend|python-backend|all)"
    Write-Host "  test [service]      Test service(s) using dev environment (frontend|java-backend|python-backend|all)"
    Write-Host "  dev-start          Start development environment with hot reload"
    Write-Host "  dev-stop           Stop development environment"
    Write-Host "  prod-start         Start production environment"
    Write-Host "  prod-stop          Stop production environment"
    Write-Host "  push               Push images to registry"
    Write-Host "  pull               Pull images from registry"
    Write-Host "  integration-test   Run integration tests using dev environment"
    Write-Host "  cleanup            Clean up containers and images"
    Write-Host "  help               Show this help message"
    Write-Host ""
    Write-Host "Parameters:" -ForegroundColor Yellow
    Write-Host "  -Version           Image version (default: latest)"
    Write-Host "  -Registry          Container registry (default: ghcr.io/lxtececo)"
    Write-Host ""
    Write-Host "Examples:" -ForegroundColor Green
    Write-Host "  .\scripts\container-manager.ps1 build"
    Write-Host "  .\scripts\container-manager.ps1 build frontend"
    Write-Host "  .\scripts\container-manager.ps1 dev-start"
    Write-Host "  .\scripts\container-manager.ps1 test all"
    Write-Host "  .\scripts\container-manager.ps1 integration-test"
    Write-Host "  .\scripts\container-manager.ps1 push -Version v1.0.0"
}

# Main script logic
switch ($Command.ToLower()) {
    "build" {
        if ($Service -eq "all") {
            Build-All
        } else {
            Build-Service $Service
        }
    }
    "test" {
        if ($Service -eq "all") {
            Test-All
        } else {
            Test-Service $Service
        }
    }
    "dev-start" { Start-Development }
    "dev-stop" { Stop-Development }
    "prod-start" { Start-Production }
    "prod-stop" { Stop-Production }
    "push" { Push-Images }
    "pull" { Pull-Images }
    "integration-test" { Invoke-IntegrationTest }
    "cleanup" { Invoke-Cleanup }
    default { Show-Usage }
}