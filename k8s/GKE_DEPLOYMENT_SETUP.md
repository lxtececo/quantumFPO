# GKE Deployment Setup Guide

This guide will help you set up automated deployment to Google Kubernetes Engine (GKE) for the Quantum Financial Portfolio Optimization application.

## 🏗️ Prerequisites

### 1. GCP Project Setup
```bash
# Create a new GCP project (optional)
gcloud projects create YOUR_PROJECT_ID --name="Quantum Portfolio Optimization"

# Set the project as default
gcloud config set project YOUR_PROJECT_ID

# Enable required APIs
gcloud services enable container.googleapis.com
gcloud services enable containerregistry.googleapis.com
gcloud services enable cloudbuild.googleapis.com
```

### 2. Create GKE Cluster
```bash
# Create a GKE cluster
gcloud container clusters create quantumfpo-cluster \
    --zone us-central1-a \
    --num-nodes 3 \
    --enable-autoscaling \
    --min-nodes 1 \
    --max-nodes 10 \
    --machine-type e2-standard-2 \
    --disk-size 100GB \
    --enable-autorepair \
    --enable-autoupgrade

# Get cluster credentials
gcloud container clusters get-credentials quantumfpo-cluster --zone us-central1-a
```

### 3. Create Service Account for GitHub Actions
```bash
# Create service account
gcloud iam service-accounts create github-actions-sa \
    --description="Service account for GitHub Actions" \
    --display-name="GitHub Actions SA"

# Add necessary roles
gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
    --member="serviceAccount:github-actions-sa@YOUR_PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/container.developer"

gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
    --member="serviceAccount:github-actions-sa@YOUR_PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/storage.admin"

# Create and download service account key
gcloud iam service-accounts keys create ~/github-actions-key.json \
    --iam-account=github-actions-sa@YOUR_PROJECT_ID.iam.gserviceaccount.com
```

## 🔐 GitHub Secrets Configuration

Add the following secrets to your GitHub repository (`Settings > Secrets and variables > Actions`):

### Required Secrets
- **`GCP_PROJECT_ID`**: Your Google Cloud Project ID
- **`GKE_CLUSTER_NAME`**: `quantumfpo-cluster` 
- **`GKE_CLUSTER_ZONE`**: `us-central1-a` (or your chosen zone)
- **`GCP_SA_KEY`**: Contents of the `~/github-actions-key.json` file

### How to add GCP_SA_KEY:
```bash
# Display the service account key (copy this to GitHub secret)
cat ~/github-actions-key.json
```

## 🚀 Deployment Workflow Features

### Automatic Triggers
- **Triggers**: After successful CI/CD pipeline completion on `main` branch
- **Environment**: Production environment with manual approval (optional)
- **Rollback**: Automatic rollback on deployment failure

### Deployment Components
1. **Python Backend**: FastAPI optimization service (2 replicas)
2. **Java Backend**: Spring Boot API gateway (2 replicas) 
3. **Frontend**: React application with Nginx (3 replicas)
4. **Ingress**: Google Cloud Load Balancer with SSL
5. **HPA**: Horizontal Pod Autoscaling based on CPU/Memory

### Health Checks & Monitoring
- **Liveness Probes**: Ensure pods restart if unhealthy
- **Readiness Probes**: Control traffic routing to healthy pods
- **Smoke Tests**: Post-deployment verification of all endpoints

## 🔧 Customization

### 1. Domain Configuration
Edit `k8s/ingress.yaml`:
```yaml
rules:
- host: your-domain.com  # Replace with your actual domain
```

### 2. Resource Limits
Adjust resources in deployment files based on your needs:
```yaml
resources:
  requests:
    memory: "512Mi"
    cpu: "250m"
  limits:
    memory: "1Gi" 
    cpu: "500m"
```

### 3. Scaling Configuration
Modify `k8s/hpa.yaml` for auto-scaling behavior:
```yaml
minReplicas: 1
maxReplicas: 10
metrics:
- type: Resource
  resource:
    name: cpu
    target:
      averageUtilization: 70
```

## 🌍 DNS and SSL Setup

### 1. Reserve Static IP
```bash
# Reserve global static IP
gcloud compute addresses create quantumfpo-ip --global

# Get the IP address
gcloud compute addresses describe quantumfpo-ip --global
```

### 2. Configure DNS
Point your domain's A record to the reserved static IP.

### 3. SSL Certificate
The deployment uses Google-managed SSL certificates that will be automatically provisioned once DNS is configured.

## 📊 Monitoring Deployment

### Check Deployment Status
```bash
# Get cluster credentials
gcloud container clusters get-credentials quantumfpo-cluster --zone us-central1-a

# Check deployments
kubectl get deployments -n quantumfpo

# Check services
kubectl get services -n quantumfpo

# Check ingress
kubectl get ingress -n quantumfpo

# Check HPA status
kubectl get hpa -n quantumfpo
```

### View Logs
```bash
# Frontend logs
kubectl logs -l app=quantumfpo-frontend -n quantumfpo

# Java backend logs  
kubectl logs -l app=quantumfpo-java-backend -n quantumfpo

# Python backend logs
kubectl logs -l app=quantumfpo-python-backend -n quantumfpo
```

### Access Application
```bash
# Get external IP
kubectl get service quantumfpo-frontend -n quantumfpo

# Or via ingress (once DNS is configured)
# https://your-domain.com
```

## 🔄 Manual Deployment

If you need to deploy manually:

```bash
# Authenticate with GCP
gcloud auth login

# Get cluster credentials
gcloud container clusters get-credentials quantumfpo-cluster --zone us-central1-a

# Deploy with specific image tags
export IMAGE_TAG="your-commit-sha"
sed -i "s|FRONTEND_IMAGE|ghcr.io/lxtececo/quantumfpo-frontend:$IMAGE_TAG|g" k8s/frontend-deployment.yaml
sed -i "s|JAVA_BACKEND_IMAGE|ghcr.io/lxtececo/quantumfpo-java-backend:$IMAGE_TAG|g" k8s/java-backend-deployment.yaml  
sed -i "s|PYTHON_BACKEND_IMAGE|ghcr.io/lxtececo/quantumfpo-python-backend:$IMAGE_TAG|g" k8s/python-backend-deployment.yaml

# Apply manifests
kubectl apply -f k8s/

# Check rollout status
kubectl rollout status deployment/quantumfpo-frontend -n quantumfpo
kubectl rollout status deployment/quantumfpo-java-backend -n quantumfpo
kubectl rollout status deployment/quantumfpo-python-backend -n quantumfpo
```

## 🚨 Troubleshooting

### Common Issues

1. **Image Pull Errors**: Ensure GitHub Container Registry authentication is configured
2. **Resource Limits**: Adjust CPU/memory requests if nodes are resource-constrained
3. **Health Check Failures**: Verify application health endpoints are working
4. **DNS Issues**: Ensure domain points to the correct static IP address

### Debug Commands
```bash
# Describe problematic pods
kubectl describe pod <pod-name> -n quantumfpo

# Get events
kubectl get events -n quantumfpo --sort-by='.lastTimestamp'

# Check resource usage
kubectl top pods -n quantumfpo
kubectl top nodes
```

## 🎯 Next Steps

1. **Set up monitoring**: Consider integrating with Google Cloud Monitoring
2. **Configure alerts**: Set up notifications for deployment failures
3. **Implement blue-green**: Add blue-green deployment strategy for zero-downtime
4. **Add persistent storage**: Configure persistent volumes for stateful components
5. **Security scanning**: Implement container scanning with Google Container Analysis

## 📚 Additional Resources

- [GKE Documentation](https://cloud.google.com/kubernetes-engine/docs)
- [Kubernetes Best Practices](https://cloud.google.com/kubernetes-engine/docs/best-practices)
- [GitHub Actions GCP Documentation](https://github.com/google-github-actions)