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

# Test individual service
function Test-Service {
    param([string]$ServiceName)
    
    $port = switch ($ServiceName) {
        "frontend" { 3000 }
        "java-backend" { 8080 }
        "python-backend" { 8002 }
        default { 
            Write-Error "Unknown service: $ServiceName"
            return $false
        }
    }
    
    $healthEndpoint = switch ($ServiceName) {
        "frontend" { "/health" }
        "java-backend" { "/actuator/health" }
        "python-backend" { "/health" }
    }
    
    Write-Log "Testing $ServiceName..."
    
    # Start container
    docker run -d --name "test-$ServiceName" -p "${port}:${port}" "${ProjectName}-${ServiceName}:${Version}"
    
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Failed to start container for $ServiceName"
        return $false
    }
    
    # Wait for container to be ready
    Write-Log "Waiting for $ServiceName to be ready..."
    Start-Sleep -Seconds 15
    
    # Test health endpoint
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:${port}${healthEndpoint}" -TimeoutSec 10
        if ($response.StatusCode -eq 200) {
            Write-Success "$ServiceName is healthy"
            $success = $true
        } else {
            Write-Error "$ServiceName health check failed with status $($response.StatusCode)"
            $success = $false
        }
    }
    catch {
        Write-Error "$ServiceName health check failed: $($_.Exception.Message)"
        docker logs "test-$ServiceName"
        $success = $false
    }
    
    # Cleanup
    docker stop "test-$ServiceName" | Out-Null
    docker rm "test-$ServiceName" | Out-Null
    
    return $success
}

# Test all services
function Test-All {
    Write-Log "Testing all services individually..."
    $success = $true
    
    foreach ($service in $Services) {
        if (-not (Test-Service $service)) {
            $success = $false
        }
    }
    
    if ($success) {
        Write-Success "All service tests passed"
    } else {
        Write-Error "Some service tests failed"
    }
}

# Start development environment
function Start-Development {
    Write-Log "Starting development environment..."
    docker-compose -f docker-compose.dev.yml up -d
    
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Failed to start development environment"
        return
    }
    
    Write-Log "Waiting for services to be ready..."
    Start-Sleep -Seconds 30
    
    Write-Log "Checking service health..."
    try { Invoke-WebRequest -Uri "http://localhost:5173/health" -TimeoutSec 5 | Out-Null } catch { Write-Warn "Frontend dev server might still be starting" }
    try { Invoke-WebRequest -Uri "http://localhost:8080/actuator/health" -TimeoutSec 5 | Out-Null } catch { Write-Warn "Java backend might still be starting" }
    try { Invoke-WebRequest -Uri "http://localhost:8002/health" -TimeoutSec 5 | Out-Null } catch { Write-Warn "Python backend might still be starting" }
    
    Write-Success "Development environment started"
    Write-Log "Frontend: http://localhost:5173"
    Write-Log "Java API: http://localhost:8080"
    Write-Log "Python API: http://localhost:8002"
}

# Stop development environment
function Stop-Development {
    Write-Log "Stopping development environment..."
    docker-compose -f docker-compose.dev.yml down
    Write-Success "Development environment stopped"
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

# Integration test
function Invoke-IntegrationTest {
    Write-Log "Running integration tests..."
    
    # Start services
    docker-compose up -d
    
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Failed to start services for integration test"
        return
    }
    
    # Wait for services
    Start-Sleep -Seconds 60
    
    # Run integration tests
    Push-Location backend
    try {
        python -m pytest src/test/python/test_integration_e2e.py -v -m "integration"
        
        if ($LASTEXITCODE -eq 0) {
            Write-Success "Integration tests passed"
        } else {
            Write-Error "Integration tests failed"
            docker-compose logs
        }
    }
    finally {
        Pop-Location
        docker-compose down | Out-Null
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
    Write-Host "  test [service]      Test service(s) (frontend|java-backend|python-backend|all)"
    Write-Host "  dev-start          Start development environment"
    Write-Host "  dev-stop           Stop development environment"
    Write-Host "  prod-start         Start production environment"
    Write-Host "  prod-stop          Stop production environment"
    Write-Host "  push               Push images to registry"
    Write-Host "  pull               Pull images from registry"
    Write-Host "  integration-test   Run integration tests"
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
    Write-Host "  .\scripts\container-manager.ps1 test all"
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