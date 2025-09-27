# Kubernetes Manifests for Quantum Portfolio Optimization

This directory contains Kubernetes manifests for deploying the Quantum Financial Portfolio Optimization application to Google Kubernetes Engine (GKE).

## 📁 File Structure

```
k8s/
├── 00-namespace-config.yaml     # Namespace, ConfigMap, and Secrets
├── python-backend-deployment.yaml   # Python FastAPI backend
├── java-backend-deployment.yaml     # Java Spring Boot backend  
├── frontend-deployment.yaml         # React frontend with Nginx
├── ingress.yaml                     # Load balancer and SSL configuration
├── hpa.yaml                         # Horizontal Pod Autoscaling
├── monitoring.yaml                  # NetworkPolicy and monitoring config
├── GKE_DEPLOYMENT_SETUP.md         # Complete setup guide
└── README.md                       # This file
```

## 🏗️ Architecture Overview

### Components
- **Frontend**: React application served by Nginx (3 replicas)
- **Java Backend**: Spring Boot API gateway (2 replicas)
- **Python Backend**: FastAPI optimization service (2 replicas)
- **Ingress**: Google Cloud Load Balancer with automatic SSL
- **HPA**: Auto-scaling based on CPU and memory usage

### Service Communication
```
Internet → Ingress → Frontend (80)
       ↘ → Java Backend (8080) → Python Backend (8002)
```

### Resource Requirements
- **Frontend**: 128Mi-256Mi RAM, 100m-200m CPU
- **Java Backend**: 512Mi-1Gi RAM, 250m-500m CPU  
- **Python Backend**: 512Mi-1Gi RAM, 250m-500m CPU

## 🚀 Quick Deployment

### Prerequisites
1. GKE cluster with at least 3 nodes
2. `kubectl` configured for your cluster
3. Container images available in GitHub Container Registry

### Deploy with specific image tags
```bash
# Set your image tag (usually commit SHA)
export IMAGE_TAG="your-commit-sha-here"

# Replace image placeholders
sed -i "s|FRONTEND_IMAGE|ghcr.io/lxtececo/quantumfpo-frontend:$IMAGE_TAG|g" k8s/frontend-deployment.yaml
sed -i "s|JAVA_BACKEND_IMAGE|ghcr.io/lxtececo/quantumfpo-java-backend:$IMAGE_TAG|g" k8s/java-backend-deployment.yaml
sed -i "s|PYTHON_BACKEND_IMAGE|ghcr.io/lxtececo/quantumfpo-python-backend:$IMAGE_TAG|g" k8s/python-backend-deployment.yaml

# Deploy all resources
kubectl apply -f k8s/

# Check deployment status
kubectl get pods -n quantumfpo
kubectl get services -n quantumfpo
kubectl get ingress -n quantumfpo
```

### Using Kustomize (Recommended)
```bash
# Deploy with Kustomize
kubectl apply -k k8s/

# Or with specific image tags
kubectl kustomize k8s/ | kubectl apply -f -
```

## 📊 Health Checks & Probes

### Endpoints
- **Frontend**: `GET /health` (port 80)
- **Java Backend**: 
  - Liveness: `GET /actuator/health` (port 8080)
  - Readiness: `GET /actuator/health/readiness` (port 8080)
- **Python Backend**: `GET /health` (port 8002)

### Probe Configuration
- **Initial Delay**: 10-60s (depending on service startup time)
- **Period**: 10-30s
- **Timeout**: 5-10s
- **Failure Threshold**: 3

## 🔄 Auto-Scaling Configuration

### Horizontal Pod Autoscaler (HPA)
- **Frontend**: 2-10 replicas (70% CPU, 80% memory)
- **Java Backend**: 1-5 replicas (70% CPU, 80% memory)
- **Python Backend**: 1-5 replicas (70% CPU, 80% memory)

### Scaling Triggers
```yaml
metrics:
- type: Resource
  resource:
    name: cpu
    target:
      averageUtilization: 70
- type: Resource  
  resource:
    name: memory
    target:
      averageUtilization: 80
```

## 🌐 Ingress & Load Balancing

### Features
- **Global Load Balancer**: Google Cloud HTTP(S) Load Balancer
- **SSL Termination**: Automatic managed certificates
- **Path-based Routing**: 
  - `/api/java/*` → Java Backend
  - `/api/python/*` → Python Backend  
  - `/*` → Frontend

### Domain Configuration
1. Reserve static IP: `gcloud compute addresses create quantumfpo-ip --global`
2. Update DNS: Point A record to the static IP
3. Update `ingress.yaml` with your domain name
4. SSL certificate will be automatically provisioned

## 🔒 Security Configuration

### Pod Security
- **Non-root users**: All containers run as non-root
- **Read-only root filesystem**: Where possible
- **No privilege escalation**: Security contexts configured
- **Network policies**: Restrict inter-pod communication

### Secrets Management
- Sensitive data stored in Kubernetes Secrets
- ConfigMap for non-sensitive configuration
- Environment-specific overrides supported

## 📈 Monitoring & Observability

### Built-in Monitoring
- **NetworkPolicy**: Controls pod-to-pod communication for security
- **ConfigMap**: Contains monitoring endpoints configuration  
- **Health Checks**: Kubernetes liveness and readiness probes
- **Resource Monitoring**: CPU and memory metrics for HPA

### Metrics Collection
- **Java Backend**: Prometheus metrics via Spring Boot Actuator (`/actuator/prometheus`)
- **Python Backend**: Health endpoint (`/health`) - ready for custom metrics
- **Frontend**: Nginx health checks

### Logging  
- All containers log to stdout/stderr
- Logs available via `kubectl logs -f deployment/<service-name> -n quantumfpo`
- Integration with Google Cloud Logging

### Advanced Monitoring (Optional)
For production monitoring with Prometheus and Grafana:
1. Install Prometheus Operator: `kubectl apply -f https://github.com/prometheus-operator/prometheus-operator/releases/download/v0.68.0/bundle.yaml`
2. Replace monitoring.yaml with ServiceMonitor resources
3. Deploy Grafana dashboards for visualization

### Service Mesh (Optional)
Ready for Istio service mesh integration for advanced traffic management and observability.

## 🔧 Customization

### Environment-Specific Deployments
```bash
# Development
kubectl apply -f k8s/ --dry-run=client -o yaml | \
  sed 's/replicas: 3/replicas: 1/' | \
  kubectl apply -f -

# Staging with resource limits
kubectl patch deployment quantumfpo-frontend -n quantumfpo -p '
{
  "spec": {
    "template": {
      "spec": {
        "containers": [
          {
            "name": "frontend",
            "resources": {
              "limits": {"memory": "128Mi", "cpu": "100m"}
            }
          }
        ]
      }
    }
  }
}'
```

### Blue-Green Deployment
```bash
# Deploy new version with suffix
kubectl apply -f k8s/ --dry-run=client -o yaml | \
  sed 's/name: quantumfpo/name: quantumfpo-green/' | \
  kubectl apply -f -

# Switch traffic via service selector update
kubectl patch service quantumfpo-frontend -n quantumfpo -p '
{
  "spec": {
    "selector": {
      "version": "green"
    }
  }
}'
```

## 🚨 Troubleshooting

### Common Issues
1. **ImagePullBackOff**: Check container registry authentication
2. **CrashLoopBackOff**: Check application logs and health checks
3. **Pending Pods**: Check node resources and pod resource requests
4. **Service Unavailable**: Verify service selectors and pod labels

### Debug Commands
```bash
# Check pod status
kubectl get pods -n quantumfpo -o wide

# Describe problematic resources
kubectl describe pod <pod-name> -n quantumfpo
kubectl describe service <service-name> -n quantumfpo

# View logs
kubectl logs -l app=quantumfpo-frontend -n quantumfpo --tail=100

# Check events
kubectl get events -n quantumfpo --sort-by='.lastTimestamp'

# Resource usage
kubectl top pods -n quantumfpo
kubectl top nodes
```

### Port Forwarding for Debug
```bash
# Frontend
kubectl port-forward service/quantumfpo-frontend 3000:80 -n quantumfpo

# Java Backend  
kubectl port-forward service/quantumfpo-java-backend 8080:8080 -n quantumfpo

# Python Backend
kubectl port-forward service/quantumfpo-python-backend 8002:8002 -n quantumfpo
```

## 📚 Additional Resources

- **Setup Guide**: [GKE_DEPLOYMENT_SETUP.md](./GKE_DEPLOYMENT_SETUP.md)
- **GitHub Actions**: [../.github/workflows/gke-deploy.yml](../.github/workflows/gke-deploy.yml)
- **Application Documentation**: [../README.md](../README.md)
- **Kubernetes Documentation**: https://kubernetes.io/docs/
- **GKE Best Practices**: https://cloud.google.com/kubernetes-engine/docs/best-practices