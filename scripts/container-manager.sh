#!/bin/bash

# Container Build and Management Scripts for QuantumFPO
# Usage: ./scripts/container-manager.sh [command]

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PROJECT_NAME="quantumfpo"
REGISTRY="ghcr.io/lxtececo"
VERSION=${VERSION:-latest}
SERVICES=("frontend" "java-backend" "python-backend")

# Helper functions
log() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

# Build individual service
build_service() {
    local service=$1
    local tag=${2:-$VERSION}
    
    log "Building $service..."
    
    case $service in
        "frontend")
            docker build -t ${PROJECT_NAME}-${service}:${tag} \
                -f frontend/Dockerfile frontend/
            ;;
        "java-backend")
            docker build -t ${PROJECT_NAME}-${service}:${tag} \
                -f backend/Dockerfile backend/
            ;;
        "python-backend")
            docker build -t ${PROJECT_NAME}-${service}:${tag} \
                -f backend/src/main/python/Dockerfile .
            ;;
        *)
            error "Unknown service: $service"
            return 1
            ;;
    esac
    
    success "Built $service successfully"
}

# Build all services
build_all() {
    log "Building all services..."
    
    for service in "${SERVICES[@]}"; do
        build_service $service
    done
    
    success "All services built successfully"
}

# Test individual service
test_service() {
    local service=$1
    local port
    local health_endpoint
    
    case $service in
        "frontend")
            port=3000
            health_endpoint="/health"
            ;;
        "java-backend")
            port=8080
            health_endpoint="/actuator/health"
            ;;
        "python-backend")
            port=8002
            health_endpoint="/health"
            ;;
        *)
            error "Unknown service: $service"
            return 1
            ;;
    esac
    
    log "Testing $service..."
    
    # Start container
    docker run -d --name test-${service} \
        -p ${port}:${port} \
        ${PROJECT_NAME}-${service}:${VERSION}
    
    # Wait for container to be ready
    log "Waiting for $service to be ready..."
    sleep 15
    
    # Test health endpoint
    if curl -f http://localhost:${port}${health_endpoint} > /dev/null 2>&1; then
        success "$service is healthy"
    else
        error "$service health check failed"
        docker logs test-${service}
        docker stop test-${service}
        docker rm test-${service}
        return 1
    fi
    
    # Cleanup
    docker stop test-${service}
    docker rm test-${service}
}

# Test all services
test_all() {
    log "Testing all services individually..."
    
    for service in "${SERVICES[@]}"; do
        test_service $service
    done
    
    success "All service tests passed"
}

# Start development environment
dev_start() {
    log "Starting development environment..."
    docker-compose -f docker-compose.dev.yml up -d
    
    log "Waiting for services to be ready..."
    sleep 30
    
    log "Checking service health..."
    curl -f http://localhost:5173/health || warn "Frontend dev server might still be starting"
    curl -f http://localhost:8080/actuator/health || warn "Java backend might still be starting"
    curl -f http://localhost:8002/health || warn "Python backend might still be starting"
    
    success "Development environment started"
    log "Frontend: http://localhost:5173"
    log "Java API: http://localhost:8080"
    log "Python API: http://localhost:8002"
}

# Stop development environment
dev_stop() {
    log "Stopping development environment..."
    docker-compose -f docker-compose.dev.yml down
    success "Development environment stopped"
}

# Start production environment
prod_start() {
    log "Starting production environment..."
    docker-compose up -d
    
    log "Waiting for services to be ready..."
    sleep 45
    
    log "Checking service health..."
    curl -f http://localhost:3000/health
    curl -f http://localhost:8080/actuator/health
    curl -f http://localhost:8002/health
    
    success "Production environment started"
    log "Frontend: http://localhost:3000"
    log "Java API: http://localhost:8080"
    log "Python API: http://localhost:8002"
}

# Stop production environment
prod_stop() {
    log "Stopping production environment..."
    docker-compose down
    success "Production environment stopped"
}

# Push images to registry
push_images() {
    log "Pushing images to registry..."
    
    for service in "${SERVICES[@]}"; do
        local local_tag="${PROJECT_NAME}-${service}:${VERSION}"
        local remote_tag="${REGISTRY}/${PROJECT_NAME}-${service}:${VERSION}"
        
        log "Tagging $service for registry..."
        docker tag $local_tag $remote_tag
        
        log "Pushing $service to registry..."
        docker push $remote_tag
        
        success "Pushed $service to registry"
    done
    
    success "All images pushed to registry"
}

# Pull images from registry
pull_images() {
    log "Pulling images from registry..."
    
    for service in "${SERVICES[@]}"; do
        local remote_tag="${REGISTRY}/${PROJECT_NAME}-${service}:${VERSION}"
        
        log "Pulling $service from registry..."
        docker pull $remote_tag
        
        # Tag as local image
        docker tag $remote_tag "${PROJECT_NAME}-${service}:${VERSION}"
        
        success "Pulled $service from registry"
    done
    
    success "All images pulled from registry"
}

# Clean up containers and images
cleanup() {
    log "Cleaning up containers and images..."
    
    # Stop and remove all project containers
    docker ps -a --filter "name=${PROJECT_NAME}" --format "{{.Names}}" | xargs -r docker stop
    docker ps -a --filter "name=${PROJECT_NAME}" --format "{{.Names}}" | xargs -r docker rm
    
    # Remove project images
    docker images --filter "reference=${PROJECT_NAME}-*" --format "{{.Repository}}:{{.Tag}}" | xargs -r docker rmi
    
    # Clean up unused resources
    docker system prune -f
    
    success "Cleanup completed"
}

# Integration test
integration_test() {
    log "Running integration tests..."
    
    # Start services
    docker-compose up -d
    
    # Wait for services
    sleep 60
    
    # Run integration tests
    cd backend
    python -m pytest src/test/python/test_integration_e2e.py -v -m "integration" || {
        error "Integration tests failed"
        docker-compose logs
        docker-compose down
        return 1
    }
    
    # Cleanup
    docker-compose down
    
    success "Integration tests passed"
}

# Show usage
usage() {
    echo "Container Management Script for QuantumFPO"
    echo ""
    echo "Usage: $0 [command] [options]"
    echo ""
    echo "Commands:"
    echo "  build [service]     Build service(s) (frontend|java-backend|python-backend|all)"
    echo "  test [service]      Test service(s) (frontend|java-backend|python-backend|all)"
    echo "  dev-start          Start development environment"
    echo "  dev-stop           Stop development environment"
    echo "  prod-start         Start production environment"
    echo "  prod-stop          Stop production environment"
    echo "  push               Push images to registry"
    echo "  pull               Pull images from registry"
    echo "  integration-test   Run integration tests"
    echo "  cleanup            Clean up containers and images"
    echo "  help               Show this help message"
    echo ""
    echo "Environment Variables:"
    echo "  VERSION            Image version (default: latest)"
    echo "  REGISTRY           Container registry (default: ghcr.io/lxtececo)"
    echo ""
    echo "Examples:"
    echo "  $0 build all                    # Build all services"
    echo "  $0 build frontend               # Build only frontend"
    echo "  $0 test all                     # Test all services"
    echo "  VERSION=v1.0.0 $0 push          # Push v1.0.0 images"
}

# Main script logic
case "${1:-help}" in
    "build")
        if [[ "$2" == "all" || -z "$2" ]]; then
            build_all
        else
            build_service "$2"
        fi
        ;;
    "test")
        if [[ "$2" == "all" || -z "$2" ]]; then
            test_all
        else
            test_service "$2"
        fi
        ;;
    "dev-start")
        dev_start
        ;;
    "dev-stop")
        dev_stop
        ;;
    "prod-start")
        prod_start
        ;;
    "prod-stop")
        prod_stop
        ;;
    "push")
        push_images
        ;;
    "pull")
        pull_images
        ;;
    "integration-test")
        integration_test
        ;;
    "cleanup")
        cleanup
        ;;
    "help"|*)
        usage
        ;;
esac