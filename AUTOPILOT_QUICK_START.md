# 🚁 GKE Autopilot Migration: Complete Alpha-Stage Cost Optimization Guide

## 📋 Executive Summary

This guide provides complete instructions for migrating your QuantumFPO application from Standard GKE to Autopilot mode with aggressive cost optimization strategies designed for alpha-stage development.

**Expected Cost Savings: 70-85% reduction**
- Autopilot vs Standard GKE: ~40-60% 
- Alpha resource optimization: ~30-50%
- Scheduled scaling: ~60-70% during off-hours
- Combined optimizations: **Total savings of $200-500/month** for typical setups

## 🎯 Quick Start (15 minutes)

### Option 1: Automated Migration (Windows PowerShell)
```powershell
# Run the automated migration script
.\scripts\autopilot\migrate-to-autopilot.ps1 -ProjectId "your-project-id" -Region "us-central1"
```

### Option 2: Automated Migration (Linux/macOS)
```bash
# Make script executable and run
chmod +x scripts/autopilot/cost-optimizer.sh
./scripts/autopilot/cost-optimizer.sh all
```

### Option 3: Manual Step-by-Step Migration
Follow the detailed instructions below.

---

## 🛠️ Detailed Manual Migration Steps

### Step 1: Prerequisites Check ✅

**Required Tools:**
```bash
# Verify tools are installed
gcloud --version    # Google Cloud CLI
kubectl version     # Kubernetes CLI
git --version       # Git (for image tags)
```

**Required Permissions:**
- GKE Admin (`roles/container.admin`)
- Compute Admin (`roles/compute.admin`) 
- Service Account Admin (`roles/iam.serviceAccountAdmin`)

### Step 2: Backup Current Setup 💾

```bash
# Create backup directory
mkdir -p backups/$(date +%Y%m%d)

# Backup current cluster configuration
kubectl get all --all-namespaces -o yaml > backups/$(date +%Y%m%d)/full-cluster-backup.yaml

# Backup quantumfpo namespace specifically  
kubectl get all -n quantumfpo -o yaml > backups/$(date +%Y%m%d)/quantumfpo-backup.yaml

# Backup persistent volumes (if any)
kubectl get pv,pvc --all-namespaces -o yaml > backups/$(date +%Y%m%d)/storage-backup.yaml

# Export current resource usage for comparison
kubectl top nodes > backups/$(date +%Y%m%d)/current-node-usage.txt
kubectl top pods -n quantumfpo > backups/$(date +%Y%m%d)/current-pod-usage.txt
```

### Step 3: Create GKE Autopilot Cluster 🏗️

```bash
# Set variables
export PROJECT_ID="your-project-id"
export REGION="us-central1"  # Choose region close to your users
export CLUSTER_NAME="quantumfpo-autopilot"

# Create Autopilot cluster with cost optimization features
gcloud container clusters create-auto $CLUSTER_NAME \
    --project=$PROJECT_ID \
    --region=$REGION \
    --release-channel=regular \
    --enable-network-policy \
    --enable-private-nodes \
    --master-ipv4-cidr-block=172.16.0.0/28 \
    --cluster-ipv4-cidr=/21 \
    --services-ipv4-cidr=/21 \
    --disk-size=50GB \
    --async

# Monitor creation progress (takes 5-10 minutes)
gcloud container operations list --filter="name~$CLUSTER_NAME"

# Wait for completion
gcloud container operations wait OPERATION_ID --region=$REGION
```

### Step 4: Configure kubectl for Autopilot 🔧

```bash
# Get cluster credentials
gcloud container clusters get-credentials $CLUSTER_NAME --region=$REGION

# Verify connection
kubectl cluster-info
kubectl get nodes

# Should show nodes with "Autopilot" in the description
kubectl describe nodes
```

### Step 5: Deploy Alpha-Optimized Manifests 📋

**Create optimized namespace:**
```yaml
# k8s-autopilot/00-namespace.yaml
apiVersion: v1
kind: Namespace
metadata:
  name: quantumfpo
  labels:
    app: quantumfpo
    environment: alpha
    cost-tier: optimized
---
apiVersion: v1
kind: ConfigMap
metadata:
  name: quantumfpo-config
  namespace: quantumfpo
data:
  PYTHON_API_BASE_URL: "http://quantumfpo-python-backend:8002"
  ENVIRONMENT: "alpha"
  LOG_LEVEL: "INFO"
```

**Deploy with minimal resources:**
```bash
# Create autopilot manifests directory
mkdir -p k8s-autopilot

# Copy optimized manifests (use the ones provided in GKE_AUTOPILOT_MIGRATION.md)
# Or use the generated ones from the PowerShell script

# Replace image placeholders with your actual images
export IMAGE_TAG=$(git rev-parse HEAD)

sed -i "s|FRONTEND_IMAGE|ghcr.io/lxtececo/quantumfpo-frontend:$IMAGE_TAG|g" k8s-autopilot/*.yaml
sed -i "s|JAVA_BACKEND_IMAGE|ghcr.io/lxtececo/quantumfpo-java-backend:$IMAGE_TAG|g" k8s-autopilot/*.yaml
sed -i "s|PYTHON_BACKEND_IMAGE|ghcr.io/lxtececo/quantumfpo-python-backend:$IMAGE_TAG|g" k8s-autopilot/*.yaml

# Deploy to cluster
kubectl apply -f k8s-autopilot/

# Wait for deployments to be ready
kubectl wait --for=condition=available --timeout=300s deployment --all -n quantumfpo
```

### Step 6: Implement Cost Optimization 💰

**A. Apply Alpha Resource Limits:**
```bash
# Use the cost optimizer script
chmod +x scripts/autopilot/cost-optimizer.sh
./scripts/autopilot/cost-optimizer.sh limits
```

**B. Set Up Scheduled Scaling (70% cost reduction off-hours):**
```bash
./scripts/autopilot/cost-optimizer.sh scale
```

**C. Configure Aggressive HPA:**
```bash
./scripts/autopilot/cost-optimizer.sh hpa
```

**D. Set Up Cost Monitoring:**
```bash
./scripts/autopilot/cost-optimizer.sh monitor
```

### Step 7: Validation & Testing 🧪

**Check deployment status:**
```bash
# View all resources
kubectl get all -n quantumfpo

# Check resource usage
kubectl top pods -n quantumfpo
kubectl top nodes

# Test application endpoints
kubectl get service quantumfpo-frontend -n quantumfpo
# Use the EXTERNAL-IP to test your application
```

**Validate cost optimization:**
```bash
./scripts/autopilot/cost-optimizer.sh summary
```

### Step 8: Set Up Monitoring & Alerts 📊

**A. Create Budget Alert:**
```bash
# Set up billing budget with alerts
gcloud billing budgets create \
    --billing-account=YOUR_BILLING_ACCOUNT_ID \
    --display-name="QuantumFPO Alpha Budget" \
    --budget-amount=50USD \
    --threshold-rule=percent=80 \
    --threshold-rule=percent=90 \
    --threshold-rule=percent=100
```

**B. Daily Cost Monitoring:**
```bash
# The cost optimizer script already sets this up
./scripts/autopilot/cost-optimizer.sh monitor
```

### Step 9: Clean Up Old Resources 🧹

**After validating the new cluster (recommend waiting 24-48 hours):**

```bash
# Switch back to old cluster context
gcloud container clusters get-credentials OLD_CLUSTER_NAME --zone=OLD_ZONE

# Delete old cluster (THIS IS PERMANENT!)
gcloud container clusters delete OLD_CLUSTER_NAME --zone=OLD_ZONE

# Clean up old static IPs (if any)
gcloud compute addresses list
gcloud compute addresses delete OLD_STATIC_IP_NAME --global

# Remove old container images (optional)
gcloud container images list-tags gcr.io/$PROJECT_ID/quantumfpo-frontend --limit=10
```

---

## 📊 Cost Optimization Features Implemented

### 1. **Autopilot Benefits (Automatic)**
- ✅ Pay-per-pod pricing model
- ✅ Automatic cluster scaling from 0
- ✅ Optimized node provisioning
- ✅ No node management overhead

### 2. **Alpha-Stage Resource Optimization**
- ✅ Minimal CPU/Memory requests (50m CPU, 64Mi RAM for frontend)
- ✅ Conservative scaling limits (max 2 replicas per service)
- ✅ High resource utilization thresholds (85-90%)

### 3. **Scheduled Cost Reduction** 
- ✅ **Scale to 0 at 8 PM weekdays** (60-70% cost reduction)
- ✅ **Scale up at 7 AM weekdays** (automatic development readiness)
- ✅ Weekend scaling (customizable)

### 4. **Intelligent Auto-Scaling**
- ✅ Conservative HPA with high thresholds
- ✅ Slow scale-down policies (prevent thrashing)
- ✅ Limited maximum replicas for cost control

### 5. **Resource Cleanup Automation**
- ✅ Daily cleanup of completed jobs
- ✅ Automatic evicted pod removal  
- ✅ Failed resource cleanup

---

## 💡 Alpha-Stage Development Best Practices

### **Development Workflow Optimizations:**

1. **Use Development Branches with Lower Resources:**
```yaml
# For feature branches, use even smaller resources
resources:
  requests:
    memory: "32Mi"
    cpu: "25m"
  limits:
    memory: "64Mi" 
    cpu: "50m"
```

2. **Implement Feature Flags:**
```yaml
env:
- name: FEATURE_QUANTUM_OPTIMIZATION
  value: "false"  # Disable expensive features in alpha
```

3. **Use Spot Instances for Batch Workloads:**
```yaml
# For data processing jobs
nodeSelector:
  cloud.google.com/gke-preemptible: "true"
tolerations:
- key: cloud.google.com/gke-preemptible
  operator: Equal
  value: "true"
  effect: NoSchedule
```

### **Cost Monitoring Dashboard:**

**Daily Cost Check:**
```bash
# Quick cost overview
kubectl get pods -n quantumfpo \
  -o custom-columns="NAME:.metadata.name,CPU_REQ:.spec.containers[0].resources.requests.cpu,MEM_REQ:.spec.containers[0].resources.requests.memory"

# Resource usage vs requests
kubectl top pods -n quantumfpo
```

**Weekly Cost Review:**
```bash
# Use the automated cost report
kubectl logs -l app=cost-monitor -n quantumfpo --tail=100
```

---

## 🎯 Expected Cost Breakdown

### **Monthly Cost Estimate (Alpha Configuration):**

| Component | Standard GKE | Autopilot Optimized | Savings |
|-----------|--------------|-------------------|---------|
| **Compute** | $150-300 | $45-90 | 70% |
| **Storage** | $20-40 | $10-20 | 50% |
| **Network** | $10-20 | $5-10 | 50% |
| **LoadBalancer** | $18 | $18 | 0% |
| **Total** | **$198-378** | **$78-138** | **65-75%** |

### **With Scheduled Scaling (Off-hours):**
- **Additional 60% reduction during off-hours (16 hours/day)**
- **Final monthly cost: $30-60** 🎉

### **Break-even Analysis:**
- **Development Team Cost**: $5,000-10,000/month
- **Infrastructure**: $30-60/month (0.3-1.2% of team cost)
- **ROI**: Excellent for alpha stage

---

## 🚨 Troubleshooting Common Issues

### **1. Pods Stuck in Pending State**
```bash
# Check resource requests - Autopilot requires explicit requests
kubectl describe pod POD_NAME -n quantumfpo

# Common fix: Add resource requests
resources:
  requests:
    memory: "64Mi"
    cpu: "50m"
    ephemeral-storage: "512Mi"
```

### **2. Security Context Errors**
```bash
# Autopilot requires non-root containers
securityContext:
  runAsNonRoot: true
  runAsUser: 1000
  allowPrivilegeEscalation: false
  readOnlyRootFilesystem: true
  capabilities:
    drop: ["ALL"]
```

### **3. Startup Probe Timeouts**
```bash
# Increase timeouts for Java applications
livenessProbe:
  initialDelaySeconds: 90  # Increased for JVM startup
  periodSeconds: 30
  timeoutSeconds: 10
```

### **4. Cost Higher Than Expected**
```bash
# Check actual resource usage
./scripts/autopilot/cost-optimizer.sh analyze

# Verify scheduled scaling is working
kubectl get cronjobs -n quantumfpo
kubectl get events -n quantumfpo | grep scale
```

---

## 📞 Support & Next Steps

### **Immediate Actions After Migration:**
1. ✅ Validate all application functionality
2. ✅ Monitor costs for 1 week
3. ✅ Adjust resource requests based on actual usage
4. ✅ Set up alerting for cost thresholds

### **Optimization Iterations:**
- **Week 1**: Monitor baseline costs and performance
- **Week 2**: Adjust resource requests based on metrics
- **Week 3**: Implement additional scheduled scaling
- **Week 4**: Evaluate moving to production-ready configuration

### **Graduation from Alpha:**
When ready to move beyond alpha stage:
1. Increase resource limits for production workloads
2. Add multiple replicas for high availability
3. Implement proper persistent storage
4. Set up comprehensive monitoring and alerting
5. Configure proper SSL certificates and custom domains

### **Additional Resources:**
- **GKE Autopilot Documentation**: https://cloud.google.com/kubernetes-engine/docs/concepts/autopilot-overview
- **Cost Optimization Guide**: https://cloud.google.com/kubernetes-engine/docs/best-practices/cost-optimization
- **Resource Management**: https://kubernetes.io/docs/concepts/configuration/manage-resources-containers/

---

## 🏆 Success Metrics

**Track these metrics to validate your migration:**

✅ **Cost Reduction**: 70-85% savings vs previous setup  
✅ **Performance**: Application response time < 2 seconds  
✅ **Reliability**: 99%+ uptime during business hours  
✅ **Developer Experience**: < 5 minutes from code to deployment  
✅ **Resource Efficiency**: > 60% CPU/Memory utilization during active hours

This comprehensive migration should provide substantial cost savings while maintaining the functionality needed for alpha-stage development. The automated scaling and optimization features will ensure you only pay for what you actually use, making it perfect for early-stage development work.