# GKE Autopilot Migration & Cost Optimization Guide

This guide provides instructions for migrating your QuantumFPO application from Standard GKE to Autopilot mode and implementing comprehensive cost optimization strategies for alpha-stage development.

## 📋 Table of Contents

1. [GKE Autopilot Overview](#gke-autopilot-overview)
2. [Migration Prerequisites](#migration-prerequisites)
3. [Autopilot Cluster Creation](#autopilot-cluster-creation)
4. [Manifest Modifications for Autopilot](#manifest-modifications-for-autopilot)
5. [Cost Optimization Strategies](#cost-optimization-strategies)
6. [Alpha-Stage Development Setup](#alpha-stage-development-setup)
7. [Monitoring & Cleanup](#monitoring--cleanup)
8. [Migration Execution](#migration-execution)

## 🚁 GKE Autopilot Overview

### Benefits for Alpha-Stage Applications
- **Zero node management**: No need to provision, configure, or maintain nodes
- **Pay-per-pod**: Only pay for resources your pods actually request
- **Automatic scaling**: Cluster scales from zero to handle workloads
- **Built-in security**: Hardened nodes with best practices by default
- **Cost optimization**: Automatic bin-packing and right-sizing

### Autopilot Limitations to Consider
- **Pod specifications**: Stricter requirements for resource requests/limits
- **Privileged containers**: Not supported (good for security)
- **Node access**: No SSH access to nodes
- **Custom node configurations**: Limited customization options

## 🔄 Migration Prerequisites

### 1. Backup Current Configuration
```bash
# Export current cluster configuration
kubectl get all --all-namespaces -o yaml > current-cluster-backup.yaml

# Backup specific namespace
kubectl get all -n quantumfpo -o yaml > quantumfpo-backup.yaml

# Export persistent data (if any)
kubectl get pv,pvc --all-namespaces -o yaml > storage-backup.yaml
```

### 2. Test Autopilot Compatibility
```bash
# Install GKE Autopilot compatibility checker
gcloud components install gke-gcloud-auth-plugin

# Validate current manifests for Autopilot compatibility
# Note: We'll modify them in the next section
```

## 🏗️ Autopilot Cluster Creation

### 1. Create Autopilot Cluster
```bash
# Set project and region variables
export PROJECT_ID="your-project-id"
export REGION="us-central1"  # Choose region close to your users
export CLUSTER_NAME="quantumfpo-autopilot"

# Create Autopilot cluster with cost optimization
gcloud container clusters create-auto $CLUSTER_NAME \
    --project=$PROJECT_ID \
    --region=$REGION \
    --release-channel=regular \
    --enable-network-policy \
    --enable-private-nodes \
    --master-ipv4-cidr-block=172.16.0.0/28 \
    --cluster-ipv4-cidr=/21 \
    --services-ipv4-cidr=/21 \
    --async

# Monitor cluster creation (takes 5-10 minutes)
gcloud container operations wait <operation-id> --region=$REGION
```

### 2. Configure kubectl for Autopilot
```bash
# Get credentials
gcloud container clusters get-credentials $CLUSTER_NAME --region=$REGION

# Verify connection
kubectl cluster-info
kubectl get nodes
```

## 📝 Manifest Modifications for Autopilot

Autopilot requires specific resource specifications. Here are the optimized manifests:

### 1. Namespace Configuration (Minimal Changes)
**File**: `k8s/00-namespace-config-autopilot.yaml`
```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: quantumfpo
  labels:
    app: quantumfpo
    environment: alpha
    cost-center: development
---
apiVersion: v1
kind: ConfigMap
metadata:
  name: quantumfpo-config
  namespace: quantumfpo
data:
  PYTHON_API_BASE_URL: "http://quantumfpo-python-backend:8002"
  JAVA_API_BASE_URL: "http://quantumfpo-java-backend:8080"
  ENVIRONMENT: "alpha"
  LOG_LEVEL: "INFO"
```

### 2. Python Backend (Autopilot Optimized)
**File**: `k8s/python-backend-autopilot.yaml`
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: quantumfpo-python-backend
  namespace: quantumfpo
  labels:
    app: quantumfpo-python-backend
    tier: backend
    cost-tier: alpha
spec:
  replicas: 1  # Start with 1 for alpha stage
  selector:
    matchLabels:
      app: quantumfpo-python-backend
  template:
    metadata:
      labels:
        app: quantumfpo-python-backend
        tier: backend
    spec:
      securityContext:
        runAsNonRoot: true
        runAsUser: 1000
        fsGroup: 2000
      containers:
      - name: python-backend
        image: PYTHON_BACKEND_IMAGE
        ports:
        - containerPort: 8002
          name: http
        env:
        - name: ENVIRONMENT
          value: "alpha"
        - name: PYTHONPATH
          value: "/app"
        # Autopilot requires explicit resource requests
        resources:
          requests:
            memory: "256Mi"    # Reduced for alpha stage
            cpu: "125m"        # Reduced for cost optimization
            ephemeral-storage: "1Gi"
          limits:
            memory: "512Mi"    # Conservative limits
            cpu: "250m"
            ephemeral-storage: "2Gi"
        # Health checks with longer timeouts for alpha
        livenessProbe:
          httpGet:
            path: /health
            port: 8002
          initialDelaySeconds: 45
          periodSeconds: 30
          timeoutSeconds: 10
        readinessProbe:
          httpGet:
            path: /health
            port: 8002
          initialDelaySeconds: 15
          periodSeconds: 15
          timeoutSeconds: 5
        # Security context
        securityContext:
          allowPrivilegeEscalation: false
          readOnlyRootFilesystem: true
          capabilities:
            drop:
            - ALL
        # Temporary directories for read-only filesystem
        volumeMounts:
        - name: tmp-volume
          mountPath: /tmp
      volumes:
      - name: tmp-volume
        emptyDir: {}
      # Node affinity for cost optimization
      affinity:
        nodeAffinity:
          preferredDuringSchedulingIgnoredDuringExecution:
          - weight: 100
            preference:
              matchExpressions:
              - key: cloud.google.com/compute-class
                operator: In
                values:
                - Balanced
---
apiVersion: v1
kind: Service
metadata:
  name: quantumfpo-python-backend
  namespace: quantumfpo
  labels:
    app: quantumfpo-python-backend
spec:
  type: ClusterIP
  ports:
  - port: 8002
    targetPort: 8002
    name: http
  selector:
    app: quantumfpo-python-backend
```

### 3. Java Backend (Autopilot Optimized)
**File**: `k8s/java-backend-autopilot.yaml`
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: quantumfpo-java-backend
  namespace: quantumfpo
  labels:
    app: quantumfpo-java-backend
    tier: backend
    cost-tier: alpha
spec:
  replicas: 1  # Single replica for alpha
  selector:
    matchLabels:
      app: quantumfpo-java-backend
  template:
    metadata:
      labels:
        app: quantumfpo-java-backend
        tier: backend
    spec:
      securityContext:
        runAsNonRoot: true
        runAsUser: 1000
        fsGroup: 2000
      containers:
      - name: java-backend
        image: JAVA_BACKEND_IMAGE
        ports:
        - containerPort: 8080
          name: http
        env:
        - name: SPRING_PROFILES_ACTIVE
          value: "autopilot"
        - name: JAVA_OPTS
          value: "-Xmx384m -Xms128m -XX:MaxMetaspaceSize=128m"  # Optimized for smaller instances
        envFrom:
        - configMapRef:
            name: quantumfpo-config
        # Autopilot resource requirements
        resources:
          requests:
            memory: "400Mi"    # Includes JVM overhead
            cpu: "125m"        # Reduced for cost
            ephemeral-storage: "1Gi"
          limits:
            memory: "768Mi"    # Conservative for alpha
            cpu: "500m"        # Burst capability
            ephemeral-storage: "2Gi"
        # Extended startup time for JVM
        livenessProbe:
          httpGet:
            path: /actuator/health
            port: 8080
          initialDelaySeconds: 90
          periodSeconds: 30
          timeoutSeconds: 10
        readinessProbe:
          httpGet:
            path: /actuator/health/readiness
            port: 8080
          initialDelaySeconds: 30
          periodSeconds: 15
          timeoutSeconds: 5
        # Security context
        securityContext:
          allowPrivilegeEscalation: false
          readOnlyRootFilesystem: true
          capabilities:
            drop:
            - ALL
        volumeMounts:
        - name: tmp-volume
          mountPath: /tmp
      volumes:
      - name: tmp-volume
        emptyDir: {}
---
apiVersion: v1
kind: Service
metadata:
  name: quantumfpo-java-backend
  namespace: quantumfpo
  labels:
    app: quantumfpo-java-backend
spec:
  type: ClusterIP
  ports:
  - port: 8080
    targetPort: 8080
    name: http
  selector:
    app: quantumfpo-java-backend
```

### 4. Frontend (Autopilot Optimized)
**File**: `k8s/frontend-autopilot.yaml`
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: quantumfpo-frontend
  namespace: quantumfpo
  labels:
    app: quantumfpo-frontend
    tier: frontend
    cost-tier: alpha
spec:
  replicas: 1  # Single replica for alpha
  selector:
    matchLabels:
      app: quantumfpo-frontend
  template:
    metadata:
      labels:
        app: quantumfpo-frontend
        tier: frontend
    spec:
      securityContext:
        runAsNonRoot: true
        runAsUser: 101  # nginx user
        fsGroup: 101
      containers:
      - name: frontend
        image: FRONTEND_IMAGE
        ports:
        - containerPort: 80
          name: http
        # Minimal resources for static content
        resources:
          requests:
            memory: "64Mi"     # Minimal for nginx
            cpu: "50m"         # Very low for static content
            ephemeral-storage: "512Mi"
          limits:
            memory: "128Mi"
            cpu: "100m"
            ephemeral-storage: "1Gi"
        livenessProbe:
          httpGet:
            path: /health
            port: 80
          initialDelaySeconds: 10
          periodSeconds: 30
        readinessProbe:
          httpGet:
            path: /health
            port: 80
          initialDelaySeconds: 5
          periodSeconds: 10
        securityContext:
          allowPrivilegeEscalation: false
          readOnlyRootFilesystem: true
          capabilities:
            drop:
            - ALL
        volumeMounts:
        - name: tmp-volume
          mountPath: /tmp
        - name: var-cache-nginx
          mountPath: /var/cache/nginx
        - name: var-run
          mountPath: /var/run
      volumes:
      - name: tmp-volume
        emptyDir: {}
      - name: var-cache-nginx
        emptyDir: {}
      - name: var-run
        emptyDir: {}
---
apiVersion: v1
kind: Service
metadata:
  name: quantumfpo-frontend
  namespace: quantumfpo
  labels:
    app: quantumfpo-frontend
spec:
  type: LoadBalancer  # Direct LoadBalancer for simplicity in alpha
  ports:
  - port: 80
    targetPort: 80
    name: http
  selector:
    app: quantumfpo-frontend
```

### 5. Horizontal Pod Autoscaler (Alpha Optimized)
**File**: `k8s/hpa-autopilot.yaml`
```yaml
# Conservative HPA for alpha stage - minimal scaling
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: quantumfpo-frontend-hpa
  namespace: quantumfpo
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: quantumfpo-frontend
  minReplicas: 1
  maxReplicas: 3  # Limited for cost control
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 80  # Higher threshold for cost
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
  behavior:
    scaleDown:
      stabilizationWindowSeconds: 300  # Slower scale down
      policies:
      - type: Percent
        value: 50
        periodSeconds: 60
    scaleUp:
      stabilizationWindowSeconds: 60
      policies:
      - type: Percent
        value: 100
        periodSeconds: 60
---
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: quantumfpo-java-backend-hpa
  namespace: quantumfpo
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: quantumfpo-java-backend
  minReplicas: 1
  maxReplicas: 2  # Very limited for alpha
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 85
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 85
---
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: quantumfpo-python-backend-hpa
  namespace: quantumfpo
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: quantumfpo-python-backend
  minReplicas: 1
  maxReplicas: 2
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 85
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 85
```

## 💰 Cost Optimization Strategies

### 1. Autopilot-Specific Optimizations

#### Right-sizing Resources
```yaml
# Use the smallest possible resource requests
resources:
  requests:
    memory: "64Mi"    # Start small
    cpu: "50m"        # Minimum viable CPU
    ephemeral-storage: "512Mi"
```

#### Spot Instances (Autopilot manages automatically)
- Autopilot automatically uses Spot instances when available
- No additional configuration needed
- Potential savings: 60-91%

### 2. Alpha-Stage Development Practices

#### A. Scheduled Scaling
**File**: `scripts/cost-optimization.yaml`
```yaml
# CronJob to scale down during off-hours
apiVersion: batch/v1
kind: CronJob
metadata:
  name: scale-down-night
  namespace: quantumfpo
spec:
  schedule: "0 18 * * 1-5"  # 6 PM weekdays
  jobTemplate:
    spec:
      template:
        spec:
          restartPolicy: OnFailure
          containers:
          - name: scaler
            image: bitnami/kubectl
            command:
            - /bin/sh
            - -c
            - |
              kubectl scale deployment quantumfpo-frontend --replicas=0 -n quantumfpo
              kubectl scale deployment quantumfpo-java-backend --replicas=0 -n quantumfpo  
              kubectl scale deployment quantumfpo-python-backend --replicas=0 -n quantumfpo
---
apiVersion: batch/v1
kind: CronJob
metadata:
  name: scale-up-morning
  namespace: quantumfpo
spec:
  schedule: "0 8 * * 1-5"   # 8 AM weekdays
  jobTemplate:
    spec:
      template:
        spec:
          restartPolicy: OnFailure
          containers:
          - name: scaler
            image: bitnami/kubectl
            command:
            - /bin/sh
            - -c
            - |
              kubectl scale deployment quantumfpo-frontend --replicas=1 -n quantumfpo
              kubectl scale deployment quantumfpo-java-backend --replicas=1 -n quantumfpo
              kubectl scale deployment quantumfpo-python-backend --replicas=1 -n quantumfpo
```

#### B. Development Environment Optimization
**File**: `k8s/dev-overlay/kustomization.yaml`
```yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization

resources:
- ../00-namespace-config-autopilot.yaml
- ../frontend-autopilot.yaml
- ../java-backend-autopilot.yaml
- ../python-backend-autopilot.yaml

patchesStrategicMerge:
- dev-resource-patch.yaml

images:
- name: FRONTEND_IMAGE
  newName: ghcr.io/lxtececo/quantumfpo-frontend
  newTag: dev
- name: JAVA_BACKEND_IMAGE  
  newName: ghcr.io/lxtececo/quantumfpo-java-backend
  newTag: dev
- name: PYTHON_BACKEND_IMAGE
  newName: ghcr.io/lxtececo/quantumfpo-python-backend
  newTag: dev
```

**File**: `k8s/dev-overlay/dev-resource-patch.yaml`
```yaml
# Further reduce resources for development
apiVersion: apps/v1
kind: Deployment
metadata:
  name: quantumfpo-python-backend
spec:
  template:
    spec:
      containers:
      - name: python-backend
        resources:
          requests:
            memory: "128Mi"
            cpu: "50m"
          limits:
            memory: "256Mi"
            cpu: "125m"
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: quantumfpo-java-backend
spec:
  template:
    spec:
      containers:
      - name: java-backend
        resources:
          requests:
            memory: "256Mi"
            cpu: "100m"
          limits:
            memory: "512Mi"
            cpu: "250m"
        env:
        - name: JAVA_OPTS
          value: "-Xmx256m -Xms128m -XX:MaxMetaspaceSize=96m"
---
apiVersion: apps/v1  
kind: Deployment
metadata:
  name: quantumfpo-frontend
spec:
  template:
    spec:
      containers:
      - name: frontend
        resources:
          requests:
            memory: "32Mi"
            cpu: "25m"
          limits:
            memory: "64Mi"
            cpu: "50m"
```

### 3. Cost Monitoring Setup

#### A. Budget Alerts
```bash
# Create budget alert
gcloud billing budgets create \
    --billing-account=BILLING_ACCOUNT_ID \
    --display-name="QuantumFPO Alpha Budget" \
    --budget-amount=50USD \
    --threshold-rule=percent=80 \
    --threshold-rule=percent=90 \
    --threshold-rule=percent=100
```

#### B. Cost Monitoring Script
**File**: `scripts/cost-monitor.sh`
```bash
#!/bin/bash

# Daily cost monitoring script for alpha stage

PROJECT_ID="your-project-id"
CLUSTER_NAME="quantumfpo-autopilot"
REGION="us-central1"

echo "=== QuantumFPO Alpha Cost Report $(date) ==="

# Cluster compute costs
echo "📊 Cluster Resource Usage:"
kubectl top nodes --use-protocol-buffers
kubectl top pods -n quantumfpo --use-protocol-buffers

# Pod resource requests vs limits
echo "🎯 Resource Efficiency:"
kubectl get pods -n quantumfpo -o custom-columns="NAME:.metadata.name,CPU_REQ:.spec.containers[*].resources.requests.cpu,MEM_REQ:.spec.containers[*].resources.requests.memory,CPU_LIM:.spec.containers[*].resources.limits.cpu,MEM_LIM:.spec.containers[*].resources.limits.memory"

# Estimated daily cost (rough calculation)
CPU_CORES=$(kubectl top nodes --no-headers | awk '{sum += $2} END {print sum}' | sed 's/m//' | awk '{print $1/1000}')
MEMORY_GB=$(kubectl top nodes --no-headers | awk '{sum += $4} END {print sum}' | sed 's/Mi//' | awk '{print $1/1024}')

echo "💰 Estimated Daily Cost (rough):"
echo "CPU Cores: $CPU_CORES"
echo "Memory GB: $MEMORY_GB"
echo "Estimated cost: \$$(echo "$CPU_CORES * 0.031611 + $MEMORY_GB * 0.004237" | bc) per day"

echo "====================================="
```

### 4. Preemptible Workload Configuration

For batch jobs and non-critical workloads:

**File**: `k8s/batch-workload-autopilot.yaml`
```yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: optimization-batch-job
  namespace: quantumfpo
spec:
  template:
    spec:
      # Tolerate preemption for cost savings
      tolerations:
      - key: cloud.google.com/gke-preemptible
        operator: Equal
        value: "true"
        effect: NoSchedule
      # Node selector for spot instances
      nodeSelector:
        cloud.google.com/gke-preemptible: "true"
      containers:
      - name: batch-optimizer
        image: PYTHON_BACKEND_IMAGE
        command: ["python", "batch_optimization.py"]
        resources:
          requests:
            memory: "512Mi"
            cpu: "250m"
          limits:
            memory: "1Gi"
            cpu: "500m"
      restartPolicy: Never
  backoffLimit: 3
```

## 📊 Monitoring & Cleanup

### 1. Cost Monitoring Dashboard

Create a simple monitoring setup:

**File**: `monitoring/cost-dashboard.yaml`
```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: cost-monitoring-config
  namespace: quantumfpo
data:
  prometheus.yml: |
    global:
      scrape_interval: 60s
    scrape_configs:
    - job_name: 'kubernetes-pods'
      kubernetes_sd_configs:
      - role: pod
        namespaces:
          names:
          - quantumfpo
      relabel_configs:
      - source_labels: [__meta_kubernetes_pod_annotation_prometheus_io_scrape]
        action: keep
        regex: true
---
apiVersion: batch/v1
kind: CronJob
metadata:
  name: weekly-cost-report
  namespace: quantumfpo
spec:
  schedule: "0 9 * * 1"  # Monday 9 AM
  jobTemplate:
    spec:
      template:
        spec:
          restartPolicy: OnFailure
          containers:
          - name: cost-reporter
            image: google/cloud-sdk:alpine
            command:
            - /bin/sh
            - -c
            - |
              # Generate weekly cost report
              gcloud logging read "resource.type=gke_cluster AND resource.labels.cluster_name=quantumfpo-autopilot" \
                --limit=1000 --format="value(timestamp,resource.labels.pod_name,jsonPayload.cost)" \
                --freshness=7d > /tmp/weekly-costs.log
              
              # Email or webhook notification can be added here
              echo "Weekly cost report generated at $(date)"
```

### 2. Automated Cleanup

**File**: `scripts/cleanup-unused-resources.sh`
```bash
#!/bin/bash

# Cleanup script for alpha environment

echo "🧹 Starting cleanup of unused resources..."

# Remove completed jobs older than 1 day  
kubectl delete job -n quantumfpo --field-selector=status.successful=1 \
  $(kubectl get job -n quantumfpo -o json | jq -r '.items[] | select(.status.completionTime and (now - (.status.completionTime | fromdateiso8601) > 86400)) | .metadata.name')

# Clean up failed pods older than 1 day
kubectl delete pod -n quantumfpo --field-selector=status.phase=Failed \
  $(kubectl get pod -n quantumfpo -o json | jq -r '.items[] | select(.status.phase=="Failed" and (.metadata.creationTimestamp | fromdateiso8601) < (now - 86400)) | .metadata.name')

# Clean up evicted pods
kubectl get pods -n quantumfpo | grep Evicted | awk '{print $1}' | xargs kubectl delete pod -n quantumfpo

# Report resource usage after cleanup
echo "📊 Resource usage after cleanup:"
kubectl top pods -n quantumfpo

echo "✅ Cleanup completed!"
```

## 🚀 Migration Execution

### Step 1: Preparation
```bash
# 1. Create new autopilot manifests directory
mkdir -p k8s-autopilot

# 2. Copy modified manifests to new directory
cp k8s/*-autopilot.yaml k8s-autopilot/

# 3. Test manifest validity
kubectl apply --dry-run=client -f k8s-autopilot/

# 4. Create Autopilot cluster (if not done already)
gcloud container clusters create-auto quantumfpo-autopilot \
    --region=us-central1 \
    --release-channel=regular
```

### Step 2: Blue-Green Migration
```bash
# 1. Deploy to Autopilot cluster
gcloud container clusters get-credentials quantumfpo-autopilot --region=us-central1

# 2. Replace image placeholders
export IMAGE_TAG=$(git rev-parse HEAD)
sed -i "s|FRONTEND_IMAGE|ghcr.io/lxtececo/quantumfpo-frontend:$IMAGE_TAG|g" k8s-autopilot/frontend-autopilot.yaml
sed -i "s|JAVA_BACKEND_IMAGE|ghcr.io/lxtececo/quantumfpo-java-backend:$IMAGE_TAG|g" k8s-autopilot/java-backend-autopilot.yaml  
sed -i "s|PYTHON_BACKEND_IMAGE|ghcr.io/lxtececo/quantumfpo-python-backend:$IMAGE_TAG|g" k8s-autopilot/python-backend-autopilot.yaml

# 3. Deploy to autopilot
kubectl apply -f k8s-autopilot/

# 4. Wait for deployment
kubectl wait --for=condition=available --timeout=300s deployment --all -n quantumfpo

# 5. Test the deployment
kubectl get service quantumfpo-frontend -n quantumfpo
# Test the external IP
```

### Step 3: Traffic Migration
```bash
# 1. Update DNS to point to new cluster's LoadBalancer IP
kubectl get service quantumfpo-frontend -n quantumfpo -o jsonpath='{.status.loadBalancer.ingress[0].ip}'

# 2. Monitor the new deployment for 24-48 hours
# 3. After validation, delete the old cluster
gcloud container clusters delete quantumfpo-cluster --zone=us-central1-a
```

### Step 4: Cost Optimization Activation
```bash
# 1. Deploy scheduled scaling
kubectl apply -f scripts/cost-optimization.yaml

# 2. Set up monitoring cron job
kubectl apply -f monitoring/cost-dashboard.yaml

# 3. Configure budget alerts
# (Follow budget creation commands above)
```

## 📈 Expected Cost Savings

### Alpha Stage Cost Structure
- **Autopilot vs Standard**: ~40-60% reduction
- **Resource right-sizing**: ~30-50% additional reduction  
- **Scheduled scaling**: ~60-70% reduction during off-hours
- **Preemptible workloads**: ~60-91% for batch processing

### Total Expected Savings: 70-85% compared to over-provisioned standard cluster

### Monthly Cost Estimate (Alpha Stage)
- **Small workload** (current config): $15-30/month
- **Medium workload** (with scaling): $30-60/month
- **High workload** (peak usage): $60-120/month

## 🔍 Validation Checklist

- [ ] Autopilot cluster created successfully
- [ ] All manifests have proper resource requests/limits
- [ ] Security contexts configured for Autopilot
- [ ] Health checks working with appropriate timeouts
- [ ] HPA configured with conservative scaling
- [ ] Scheduled scaling deployed for off-hours
- [ ] Cost monitoring and alerting configured
- [ ] Cleanup jobs scheduled
- [ ] Application functionality verified
- [ ] Performance acceptable for alpha stage
- [ ] Cost savings validated against previous setup

## 📞 Troubleshooting

### Common Autopilot Issues
1. **Resource requests required**: All containers must have resource requests
2. **Security context requirements**: Non-root users, no privileged containers
3. **Ephemeral storage**: Must be specified in resource requests
4. **Startup times**: Java applications may need longer initialDelaySeconds

### Cost Optimization Issues
1. **Over-scaling**: Monitor HPA behavior and adjust thresholds
2. **Unused resources**: Regular cleanup of completed jobs and failed pods
3. **Underutilized cluster**: Consider consolidating workloads

This comprehensive guide should help you migrate to GKE Autopilot while maximizing cost savings for your alpha-stage application. The estimated cost reduction should be substantial while maintaining the functionality needed for development and testing.