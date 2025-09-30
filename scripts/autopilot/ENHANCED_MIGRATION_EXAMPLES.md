# Enhanced GKE Autopilot Migration Script Examples

This document provides examples of using the enhanced PowerShell migration script with various scenarios.

## Script Location
```powershell
.\scripts\autopilot\migrate-to-autopilot.ps1
```

## Quick Reference

### Basic Parameters
- **ProjectId**: Google Cloud Project ID
- **Region**: GCP Region (e.g., us-central1, us-east1)
- **ClusterName**: Name for the new Autopilot cluster
- **Namespace**: Kubernetes namespace (default: quantumfpo)

### Enhanced Parameters
- **ExistingClusterName**: Name of existing cluster to manage
- **ExistingClusterAction**: Action to take (backup, delete, replace, ignore)
  - `backup`: Backup existing cluster, then continue with normal migration
  - `delete`: Delete existing cluster only (no new cluster created)
  - `replace`: Backup + delete existing, then create new autopilot cluster
  - `ignore`: Skip existing cluster management, create new cluster
- **EnableCostOptimization**: Apply aggressive cost reduction features
- **ImageTag**: Container image tag (default: latest)
- **NetworkTags**: Network tags for GKE cluster

## Usage Examples

### 1. Basic New Cluster Creation
Create a fresh Autopilot cluster with cost optimization:

```powershell
.\scripts\autopilot\migrate-to-autopilot.ps1 `
    -ProjectId "my-gcp-project" `
    -Region "us-central1" `
    -ClusterName "quantumfpo-autopilot" `
    -EnableCostOptimization
```

**What this does:**
- Creates new GKE Autopilot cluster
- Deploys alpha-optimized application manifests
- Applies scheduled scaling (down at 8 PM, up at 7 AM weekdays)
- Configures cost-optimized HPA settings
- Sets up daily cost monitoring

### 2. Replace Existing Standard Cluster
Backup and replace an existing Standard GKE cluster with Autopilot:

```powershell
.\scripts\autopilot\migrate-to-autopilot.ps1 `
    -ProjectId "my-gcp-project" `
    -Region "us-central1" `
    -ClusterName "quantumfpo-autopilot" `
    -ExistingClusterName "quantumfpo-standard" `
    -ExistingClusterAction "replace" `
    -EnableCostOptimization
```

**What this does:**
- Discovers existing "quantumfpo-standard" cluster
- Creates comprehensive backup of cluster configuration
- Safely deletes the old standard cluster
- Creates new Autopilot cluster "quantumfpo-autopilot"
- Applies all cost optimization features
- Shows migration summary with savings estimate

### 3. Delete Existing Cluster Only
Just delete an existing cluster without creating a new one:

```powershell
.\scripts\autopilot\migrate-to-autopilot.ps1 `
    -ProjectId "my-gcp-project" `
    -Region "us-central1" `
    -ClusterName "quantumfpo-autopilot" `
    -ExistingClusterName "quantumfpo-old" `
    -ExistingClusterAction "delete"
```

**What this does:**
- Creates backup of existing cluster (safety measure)
- Deletes the existing cluster completely
- **Does NOT create any new cluster**
- Exits after successful deletion
- Perfect for cleanup operations

### 4. Backup Only (Safety First)
Just backup an existing cluster without making changes:

```powershell
.\scripts\autopilot\migrate-to-autopilot.ps1 `
    -ProjectId "my-gcp-project" `
    -Region "us-central1" `
    -ClusterName "quantumfpo-autopilot" `
    -ExistingClusterName "quantumfpo-prod" `
    -ExistingClusterAction "backup"
```

**What this does:**
- Creates backup of existing cluster in `cluster-backups/` directory
- Includes: cluster config, node pools, deployments, services, secrets, configmaps
- Continues with normal migration process

### 5. Ignore Existing Cluster
Create new cluster while ignoring existing one:

```powershell
.\scripts\autopilot\migrate-to-autopilot.ps1 `
    -ProjectId "my-gcp-project" `
    -Region "us-central1" `
    -ClusterName "quantumfpo-new" `
    -ExistingClusterName "quantumfpo-old" `
    -ExistingClusterAction "ignore" `
    -EnableCostOptimization
```

**What this does:**
- Acknowledges existing cluster exists but takes no action
- Creates new Autopilot cluster alongside existing one
- Useful for running parallel environments

### 6. Development Environment Setup
Create cost-optimized development environment:

```powershell
.\scripts\autopilot\migrate-to-autopilot.ps1 `
    -ProjectId "quantumfpo-dev" `
    -Region "us-west1" `
    -ClusterName "quantumfpo-dev-autopilot" `
    -Namespace "dev" `
    -ImageTag "dev-latest" `
    -EnableCostOptimization `
    -NetworkTags @("dev-cluster", "alpha-stage")
```

**What this does:**
- Creates development-specific cluster
- Uses "dev" namespace
- Deploys "dev-latest" image tags
- Applies aggressive cost controls (perfect for alpha stage)
- Tags cluster for network policies

### 7. Production Migration (Conservative)
Migrate production with backup but no cost optimization:

```powershell
.\scripts\autopilot\migrate-to-autopilot.ps1 `
    -ProjectId "quantumfpo-prod" `
    -Region "us-east1" `
    -ClusterName "quantumfpo-prod-autopilot" `
    -ExistingClusterName "quantumfpo-prod-std" `
    -ExistingClusterAction "backup" `
    -Namespace "production" `
    -ImageTag "v1.2.3"
```

**Note:** Cost optimization disabled for production to maintain stability.

## Interactive Mode Examples

### List Available Clusters First
```powershell
# The script automatically discovers and shows available clusters
.\scripts\autopilot\migrate-to-autopilot.ps1 `
    -ProjectId "my-gcp-project" `
    -Region "us-central1" `
    -ClusterName "new-cluster" `
    -ExistingClusterName "nonexistent-cluster" `
    -ExistingClusterAction "backup"

# Output will show:
# ❌ Existing cluster 'nonexistent-cluster' not found
# Available clusters:
#   - quantumfpo-standard (Standard GKE) in us-central1
#   - old-dev-cluster (Standard GKE) in us-west1
```

### Confirmation Prompts
The script includes safety prompts for destructive actions:

```
⚠️  WARNING: This will permanently delete cluster 'quantumfpo-standard'
    Cluster details:
    - Name: quantumfpo-standard
    - Type: Standard GKE  
    - Region: us-central1
    - Node count: 3

Are you absolutely sure? Type 'DELETE' to confirm: DELETE
```

## Cost Optimization Features

When `-EnableCostOptimization` is used, the script applies:

### 1. Scheduled Scaling
- **Scale Down**: 8 PM weekdays (replicas → 0)  
- **Scale Up**: 7 AM weekdays (replicas → 1)
- **Weekend**: Remains scaled down
- **Estimated Savings**: 70% during off-hours

### 2. Aggressive HPA Settings
- **CPU Target**: 85-90% (vs standard 50-70%)
- **Memory Target**: 85-90% (vs standard 50-70%)
- **Max Replicas**: 2 (vs standard 10+)
- **Estimated Savings**: 30% on resource over-provisioning

### 3. Daily Cost Monitoring
- **Schedule**: 9 AM daily reports
- **Includes**: Resource usage, HPA status, cost projections
- **Output**: kubectl logs for cost-reporter pods

### 4. Right-sized Resource Requests
Applied automatically to deployment manifests:
```yaml
resources:
  requests:
    cpu: 100m      # Minimal for alpha
    memory: 128Mi  # Sufficient for development
  limits:
    cpu: 500m      # Prevent resource hogging  
    memory: 512Mi  # Alpha-appropriate limits
```

## Output Examples

### Successful Migration Output
```
🎉 MIGRATION COMPLETED SUCCESSFULLY!
=================================

📋 Migration Summary:
   From: quantumfpo-standard (Standard GKE)
   To: quantumfpo-autopilot (Autopilot GKE)  
   Region: us-central1
   Namespace: quantumfpo

✅ Completed Actions:
   ✓ Autopilot cluster created
   ✓ Alpha-optimized manifests deployed
   ✓ Application health verified
   ✓ Cost optimization enabled (scheduled scaling, HPA, monitoring)
   ✓ Original cluster configuration backed up
   ✓ Original cluster deleted

🎯 Next Steps:
   1. Test application functionality thoroughly
   2. Monitor costs for the first week
   3. Adjust resource limits based on usage patterns
   4. Set up alerting for cost thresholds
   5. Update DNS/domain settings if needed

📊 Migration Savings Estimate:
   Standard GKE (estimated): ~$126.50/month
   Autopilot optimized: ~$25.30/month
   Monthly savings: ~$101.20
   Annual savings: ~$1,214.40
```

### Cost Estimate Output
```
💰 Current Configuration:
   CPU Cores: 0.3 (~$7.24/month)
   Memory GB: 1.5 (~$19.06/month)  
   Base Cost: ~$26.30/month

📉 With Optimizations:
   Scheduled scaling (70% off-hours): ~$7.89/month
   Resource right-sizing (30% reduction): ~$18.41/month
   Combined optimizations: ~$5.26/month

📊 Migration Savings Estimate:
   Standard GKE (estimated): ~$65.75/month
   Autopilot optimized: ~$5.26/month
   Monthly savings: ~$60.49
   Annual savings: ~$725.88
```

## Troubleshooting

### Common Issues and Solutions

#### 1. Cluster Not Found
```
❌ Existing cluster 'my-cluster' not found
```
**Solution**: Run without ExistingClusterName first to see available clusters.

#### 2. Insufficient Permissions
```
❌ Failed to delete existing cluster
```
**Solution**: Ensure your account has `container.clusters.delete` permission.

#### 3. Backup Directory Issues
```
⚠️  Backup directory already exists: cluster-backups/my-cluster-20241223-143022
```
**Solution**: The script automatically handles this, or manually clean old backups.

#### 4. Cost Optimization Failures
```
⚠️  Some cost optimization features failed to apply: 
```
**Solution**: This is non-fatal. The migration continues without cost optimization.

### Getting Help
1. **Check logs**: The script provides detailed error output
2. **Verify prerequisites**: Ensure gcloud, kubectl are properly configured
3. **Check permissions**: Verify GCP IAM roles
4. **Review documentation**: See `GKE_AUTOPILOT_MIGRATION.md` for detailed guidance

## Best Practices for Alpha Stage

### 1. Use Cost Optimization
For alpha development, always use `-EnableCostOptimization`:
- Saves 70-85% on infrastructure costs
- Appropriate resource limits for development workloads
- Automatic scaling for off-hours

### 2. Regular Backups
Before any major changes:
```powershell
.\scripts\autopilot\migrate-to-autopilot.ps1 `
    -ExistingClusterAction "backup" `
    # ... other params
```

### 3. Monitor Costs
After migration:
- Check daily cost reports: `kubectl logs -l app=cost-monitor -n quantumfpo`
- Review actual vs estimated costs weekly
- Adjust resource requests based on real usage

### 4. Gradual Scaling
Start with minimal resources and scale up based on actual needs:
- Begin with cost optimization enabled
- Monitor performance for 1-2 weeks  
- Adjust resource requests and HPA settings as needed
- Disable cost optimization when moving toward production

This approach ensures maximum cost savings during alpha development while maintaining the flexibility to scale appropriately as the application matures.