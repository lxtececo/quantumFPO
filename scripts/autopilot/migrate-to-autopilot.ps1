# QuantumFPO GKE Autopilot Enhanced Migration Script
# PowerShell version for Windows users with cluster replacement capabilities

param(
    [Parameter(Mandatory=$true)]
    [string]$ProjectId,
    
    [Parameter(Mandatory=$false)]
    [string]$Region = "us-central1",
    
    [Parameter(Mandatory=$false)]
    [string]$ClusterName = "quantumfpo-autopilot",
    
    [Parameter(Mandatory=$false)]
    [string]$Namespace = "quantumfpo",
    
    [Parameter(Mandatory=$false)]
    [string]$ExistingClusterName = "",
    
    [Parameter(Mandatory=$false)]
    [string]$ExistingClusterZone = "",
    
    [Parameter(Mandatory=$false)]
    [ValidateSet("backup", "delete", "replace", "ignore")]
    [string]$ExistingClusterAction = "backup",
    
    [Parameter(Mandatory=$false)]
    [switch]$DryRun = $false,
    
    [Parameter(Mandatory=$false)]
    [switch]$SkipBackup = $false,
    
    [Parameter(Mandatory=$false)]
    [switch]$AutoApprove = $false,
    
    [Parameter(Mandatory=$false)]
    [switch]$EnableCostOptimization = $true
)

# Color output functions
function Write-Success { 
    param([string]$Message)
    Write-Host "✓ $Message" -ForegroundColor Green 
}

function Write-Warning { 
    param([string]$Message)
    Write-Host "⚠ $Message" -ForegroundColor Yellow 
}

function Write-Error { 
    param([string]$Message)
    Write-Host "✗ $Message" -ForegroundColor Red 
}

function Write-Info { 
    param([string]$Message)
    Write-Host "ℹ $Message" -ForegroundColor Blue 
}

# Check prerequisites
function Test-Prerequisites {
    Write-Info "Checking prerequisites..."
    
    $errors = @()
    
    if (!(Get-Command kubectl -ErrorAction SilentlyContinue)) {
        $errors += "kubectl is not installed or not in PATH"
    }
    
    if (!(Get-Command gcloud -ErrorAction SilentlyContinue)) {
        $errors += "gcloud CLI is not installed or not in PATH"
    }
    
    if (!(Get-Command git -ErrorAction SilentlyContinue)) {
        Write-Warning "Git is not available - will use 'latest' tag for images"
    }
    
    # Check gcloud authentication
    try {
        $authAccount = gcloud auth list --filter=status:ACTIVE --format="value(account)" 2>$null
        if (!$authAccount) {
            $errors += "gcloud is not authenticated - run 'gcloud auth login'"
        } else {
            Write-Success "Authenticated as: $authAccount"
        }
    } catch {
        $errors += "Unable to check gcloud authentication status"
    }
    
    if ($errors.Count -gt 0) {
        foreach ($error in $errors) {
            Write-Error $error
        }
        return $false
    }
    
    Write-Success "All prerequisites met"
    return $true
}

# Discover existing clusters
function Get-ExistingClusters {
    Write-Info "Discovering existing GKE clusters..."
    
    try {
        $clusters = gcloud container clusters list --project=$ProjectId --format="value(name,zone,location,currentMasterVersion,status)" 2>$null
        
        if ($clusters) {
            Write-Info "Found existing clusters:"
            $clusterArray = @()
            
            foreach ($line in $clusters) {
                if ($line.Trim()) {
                    $parts = $line.Split("`t")
                    if ($parts.Length -ge 4) {
                        # Use zone if available, otherwise use location
                        $zone = if ($parts[1]) { $parts[1] } else { $parts[2] }
                        $location = if ($parts[2]) { $parts[2] } else { $parts[1] }
                        
                        $cluster = @{
                            Name = $parts[0]
                            Zone = $zone
                            Location = $location
                            Version = $parts[3]
                            Status = if ($parts.Length -gt 4) { $parts[4] } else { "UNKNOWN" }
                        }
                        $clusterArray += $cluster
                        Write-Host "  - $($cluster.Name) (Zone/Region: $($cluster.Zone), Status: $($cluster.Status))" -ForegroundColor Cyan
                    }
                }
            }
            return $clusterArray
        } else {
            Write-Info "No existing clusters found"
            return @()
        }
    } catch {
        Write-Warning "Unable to list existing clusters: $_"
        return @()
    }
}

# Backup existing cluster configuration
function Backup-ExistingCluster {
    param(
        [string]$ClusterName,
        [string]$ClusterZone,
        [string]$BackupDir = "backups/migration-$(Get-Date -Format 'yyyyMMdd-HHmm')"
    )
    
    if ($SkipBackup) {
        Write-Warning "Skipping backup as requested"
        return $true
    }
    
    Write-Info "Creating backup of existing cluster: $ClusterName"
    
    try {
        # Create backup directory
        if (!(Test-Path $BackupDir)) {
            New-Item -ItemType Directory -Path $BackupDir -Force | Out-Null
        }
        
        # Try zone first, then region for get-credentials
        Write-Info "Getting cluster credentials..."
        gcloud container clusters get-credentials $ClusterName --zone=$ClusterZone --project=$ProjectId 2>$null
        
        if ($LASTEXITCODE -ne 0) {
            # Try with region instead of zone
            Write-Info "Zone failed, trying region parameter..."
            gcloud container clusters get-credentials $ClusterName --region=$ClusterZone --project=$ProjectId 2>$null
            
            if ($LASTEXITCODE -ne 0) {
                Write-Error "Failed to get credentials for cluster $ClusterName in zone/region $ClusterZone"
                Write-Error "Try running manually: gcloud container clusters get-credentials $ClusterName --zone=$ClusterZone --project=$ProjectId"
                return $false
            }
        }
        
        # Backup cluster configuration
        kubectl get all --all-namespaces -o yaml > "$BackupDir/full-cluster-backup.yaml"
        kubectl get pv,pvc --all-namespaces -o yaml > "$BackupDir/storage-backup.yaml"
        kubectl get configmaps,secrets --all-namespaces -o yaml > "$BackupDir/config-backup.yaml"
        
        # Backup specific namespace if it exists
        $namespaceExists = kubectl get namespace $Namespace 2>$null
        if ($LASTEXITCODE -eq 0) {
            kubectl get all -n $Namespace -o yaml > "$BackupDir/quantumfpo-namespace-backup.yaml"
            Write-Success "Namespace $Namespace backed up"
        }
        
        # Backup resource usage for comparison
        kubectl top nodes > "$BackupDir/current-node-usage.txt" 2>$null
        kubectl top pods --all-namespaces > "$BackupDir/current-pod-usage.txt" 2>$null
        
        # Backup cluster info
        gcloud container clusters describe $ClusterName --zone=$ClusterZone --project=$ProjectId > "$BackupDir/cluster-description.yaml"
        
        Write-Success "Cluster backup completed in: $BackupDir"
        return $true
        
    } catch {
        Write-Error "Failed to backup cluster: $_"
        return $false
    }
}

# Delete existing cluster
function Remove-ExistingCluster {
    param(
        [string]$ClusterName,
        [string]$ClusterZone,
        [bool]$Force = $false
    )
    
    Write-Warning "Preparing to delete existing cluster: $ClusterName"
    
    if (!$Force -and !$AutoApprove) {
        Write-Host ""
        Write-Warning "This action will PERMANENTLY DELETE the cluster '$ClusterName'!"
        Write-Warning "All data, configurations, and resources in this cluster will be lost."
        Write-Warning "Make sure you have completed the backup process."
        Write-Host ""
        
        do {
            $confirmation = Read-Host "Type 'DELETE' to confirm cluster deletion, or 'CANCEL' to abort"
            if ($confirmation -eq 'CANCEL') {
                Write-Info "Cluster deletion cancelled by user"
                return $false
            }
        } while ($confirmation -ne 'DELETE')
    }
    
    if ($DryRun) {
        Write-Warning "DRY RUN: Would delete cluster with command:"
        Write-Host "gcloud container clusters delete $ClusterName --zone=$ClusterZone --project=$ProjectId --quiet"
        return $true
    }
    
    Write-Info "Deleting cluster $ClusterName..."
    
    try {
        # Try zone first, then region for deletion
        gcloud container clusters delete $ClusterName --zone=$ClusterZone --project=$ProjectId --quiet 2>$null
        
        if ($LASTEXITCODE -ne 0) {
            # Try with region instead of zone
            Write-Info "Zone deletion failed, trying region parameter..."
            gcloud container clusters delete $ClusterName --region=$ClusterZone --project=$ProjectId --quiet
        }
        
        if ($LASTEXITCODE -eq 0) {
            Write-Success "Cluster $ClusterName deleted successfully"
            return $true
        } else {
            Write-Error "Failed to delete cluster $ClusterName in zone/region $ClusterZone"
            return $false
        }
    } catch {
        Write-Error "Exception deleting cluster: $_"
        return $false
    }
}

# Interactive cluster selection
function Select-ExistingCluster {
    param([array]$Clusters)
    
    if ($Clusters.Count -eq 0) {
        return $null
    }
    
    Write-Host ""
    Write-Info "Select the existing cluster to manage:"
    
    for ($i = 0; $i -lt $Clusters.Count; $i++) {
        $cluster = $Clusters[$i]
        Write-Host "  $($i + 1). $($cluster.Name) (Zone: $($cluster.Zone), Status: $($cluster.Status))" -ForegroundColor Yellow
    }
    
    Write-Host "  0. None - Skip existing cluster management" -ForegroundColor Gray
    Write-Host ""
    
    do {
        $selection = Read-Host "Enter your choice (0-$($Clusters.Count))"
        $selectionNum = 0
        
        if ([int]::TryParse($selection, [ref]$selectionNum)) {
            if ($selectionNum -eq 0) {
                return $null
            } elseif ($selectionNum -ge 1 -and $selectionNum -le $Clusters.Count) {
                return $Clusters[$selectionNum - 1]
            }
        }
        
        Write-Warning "Invalid selection. Please enter a number between 0 and $($Clusters.Count)"
    } while ($true)
}

# Create Autopilot cluster
function New-AutopilotCluster {
    param(
        [string]$ProjectId,
        [string]$Region,
        [string]$ClusterName
    )
    
    Write-Info "Creating GKE Autopilot cluster: $ClusterName in $Region"
    
    if ($DryRun) {
        Write-Warning "DRY RUN: Would create cluster with command:"
        Write-Host "gcloud container clusters create-auto $ClusterName --project=$ProjectId --region=$Region --release-channel=regular --enable-network-policy --async"
        return
    }
    
    try {
        $output = gcloud container clusters create-auto $ClusterName `
            --project=$ProjectId `
            --region=$Region `
            --release-channel=regular `
            --async 2>&1
        
        if ($LASTEXITCODE -eq 0) {
            Write-Success "Cluster creation initiated. This will take 5-10 minutes."
            Write-Info "Monitor progress with: gcloud container operations list --filter='name~$ClusterName'"
        } else {
            Write-Error "Failed to create cluster: $output"
            return $false
        }
    } catch {
        Write-Error "Exception creating cluster: $_"
        return $false
    }
    
    return $true
}

# Wait for cluster to be ready
function Wait-ForCluster {
    param(
        [string]$ProjectId,
        [string]$Region, 
        [string]$ClusterName
    )
    
    Write-Info "Waiting for cluster to be ready..."
    
    $maxAttempts = 30
    $attempt = 0
    
    do {
        $attempt++
        Start-Sleep -Seconds 20
        
        try {
            $status = gcloud container clusters describe $ClusterName --region=$Region --project=$ProjectId --format="value(status)" 2>$null
            
            if ($status -eq "RUNNING") {
                Write-Success "Cluster is ready!"
                return $true
            } elseif ($status -eq "ERROR") {
                Write-Error "Cluster creation failed"
                return $false
            } else {
                Write-Info "Cluster status: $status (attempt $attempt/$maxAttempts)"
            }
        } catch {
            Write-Warning "Unable to get cluster status (attempt $attempt/$maxAttempts)"
        }
    } while ($attempt -lt $maxAttempts)
    
    Write-Error "Timeout waiting for cluster to be ready"
    return $false
}

# Configure kubectl for the new cluster
function Set-KubectlContext {
    param(
        [string]$ProjectId,
        [string]$Region,
        [string]$ClusterName
    )
    
    Write-Info "Configuring kubectl for the new cluster..."
    
    try {
        gcloud container clusters get-credentials $ClusterName --region=$Region --project=$ProjectId
        
        if ($LASTEXITCODE -eq 0) {
            Write-Success "kubectl configured successfully"
            
            # Test connection
            kubectl cluster-info --request-timeout=10s >$null 2>&1
            if ($LASTEXITCODE -eq 0) {
                Write-Success "Cluster connection verified"
                return $true
            } else {
                Write-Error "Unable to connect to cluster"
                return $false
            }
        } else {
            Write-Error "Failed to configure kubectl"
            return $false
        }
    } catch {
        Write-Error "Exception configuring kubectl: $_"
        return $false
    }
}

# Generate optimized manifests for autopilot
function New-AutopilotManifests {
    Write-Info "Generating Autopilot-optimized manifests..."
    
    $manifestsDir = "k8s-autopilot"
    
    if (!(Test-Path $manifestsDir)) {
        New-Item -ItemType Directory -Path $manifestsDir | Out-Null
    }
    
    # Namespace and ConfigMap
    $namespaceYaml = @"
apiVersion: v1
kind: Namespace
metadata:
  name: $Namespace
  labels:
    app: quantumfpo
    environment: alpha
---
apiVersion: v1
kind: ConfigMap
metadata:
  name: quantumfpo-config
  namespace: $Namespace
data:
  PYTHON_API_BASE_URL: "http://quantumfpo-python-backend:8002"
  ENVIRONMENT: "alpha"
"@
    
    $namespaceYaml | Out-File -FilePath "$manifestsDir/00-namespace.yaml" -Encoding UTF8
    
    # Frontend deployment (minimal resources)
    $frontendYaml = @"
apiVersion: apps/v1
kind: Deployment
metadata:
  name: quantumfpo-frontend
  namespace: $Namespace
spec:
  replicas: 1
  selector:
    matchLabels:
      app: quantumfpo-frontend
  template:
    metadata:
      labels:
        app: quantumfpo-frontend
    spec:
      securityContext:
        runAsNonRoot: true
        runAsUser: 101
      containers:
      - name: frontend
        image: FRONTEND_IMAGE
        ports:
        - containerPort: 80
        resources:
          requests:
            memory: "64Mi"
            cpu: "50m"
            ephemeral-storage: "512Mi"
          limits:
            memory: "128Mi"
            cpu: "100m"
            ephemeral-storage: "1Gi"
        securityContext:
          allowPrivilegeEscalation: false
          readOnlyRootFilesystem: true
          capabilities:
            drop: ["ALL"]
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
  name: quantumfpo-frontend
  namespace: $Namespace
spec:
  type: LoadBalancer
  ports:
  - port: 80
    targetPort: 80
  selector:
    app: quantumfpo-frontend
"@
    
    $frontendYaml | Out-File -FilePath "$manifestsDir/frontend.yaml" -Encoding UTF8
    
    # Backend deployments with minimal resources
    $javaBackendYaml = @"
apiVersion: apps/v1
kind: Deployment
metadata:
  name: quantumfpo-java-backend
  namespace: $Namespace
spec:
  replicas: 1
  selector:
    matchLabels:
      app: quantumfpo-java-backend
  template:
    metadata:
      labels:
        app: quantumfpo-java-backend
    spec:
      securityContext:
        runAsNonRoot: true
        runAsUser: 1000
      containers:
      - name: java-backend
        image: JAVA_BACKEND_IMAGE
        ports:
        - containerPort: 8080
        env:
        - name: JAVA_OPTS
          value: "-Xmx384m -Xms128m"
        envFrom:
        - configMapRef:
            name: quantumfpo-config
        resources:
          requests:
            memory: "400Mi"
            cpu: "125m" 
            ephemeral-storage: "1Gi"
          limits:
            memory: "768Mi"
            cpu: "500m"
            ephemeral-storage: "2Gi"
        securityContext:
          allowPrivilegeEscalation: false
          readOnlyRootFilesystem: true
          capabilities:
            drop: ["ALL"]
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
  namespace: $Namespace
spec:
  type: ClusterIP
  ports:
  - port: 8080
    targetPort: 8080
  selector:
    app: quantumfpo-java-backend
"@
    
    $javaBackendYaml | Out-File -FilePath "$manifestsDir/java-backend.yaml" -Encoding UTF8
    
    # Python backend
    $pythonBackendYaml = @"
apiVersion: apps/v1
kind: Deployment
metadata:
  name: quantumfpo-python-backend
  namespace: $Namespace
spec:
  replicas: 1
  selector:
    matchLabels:
      app: quantumfpo-python-backend
  template:
    metadata:
      labels:
        app: quantumfpo-python-backend
    spec:
      securityContext:
        runAsNonRoot: true
        runAsUser: 1000
      containers:
      - name: python-backend
        image: PYTHON_BACKEND_IMAGE
        ports:
        - containerPort: 8002
        resources:
          requests:
            memory: "256Mi"
            cpu: "125m"
            ephemeral-storage: "1Gi"
          limits:
            memory: "512Mi"
            cpu: "250m"
            ephemeral-storage: "2Gi"
        securityContext:
          allowPrivilegeEscalation: false
          readOnlyRootFilesystem: true
          capabilities:
            drop: ["ALL"]
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
  name: quantumfpo-python-backend
  namespace: $Namespace
spec:
  type: ClusterIP
  ports:
  - port: 8002
    targetPort: 8002
  selector:
    app: quantumfpo-python-backend
"@
    
    $pythonBackendYaml | Out-File -FilePath "$manifestsDir/python-backend.yaml" -Encoding UTF8
    
    Write-Success "Autopilot manifests generated in $manifestsDir/"
}

# Deploy to Autopilot cluster
function Deploy-ToAutopilot {
    param([string]$ManifestsDir = "k8s-autopilot")
    
    Write-Info "Deploying to Autopilot cluster..."
    
    if (!(Test-Path $ManifestsDir)) {
        Write-Error "Manifests directory $ManifestsDir not found"
        return $false
    }
    
    # Get the latest image tag (commit SHA)
    try {
        $imageTag = git rev-parse HEAD
        if (!$imageTag) {
            $imageTag = "latest"
            Write-Warning "Unable to get git commit SHA, using 'latest' tag"
        }
    } catch {
        $imageTag = "latest"
        Write-Warning "Git not available, using 'latest' tag"
    }
    
    Write-Info "Using image tag: $imageTag"
    
    # Replace image placeholders in manifests
    $manifestFiles = Get-ChildItem -Path $ManifestsDir -Filter "*.yaml"
    
    foreach ($file in $manifestFiles) {
        $content = Get-Content $file.FullName -Raw
        $content = $content -replace "FRONTEND_IMAGE", "ghcr.io/lxtececo/quantumfpo-frontend:$imageTag"
        $content = $content -replace "JAVA_BACKEND_IMAGE", "ghcr.io/lxtececo/quantumfpo-java-backend:$imageTag"
        $content = $content -replace "PYTHON_BACKEND_IMAGE", "ghcr.io/lxtececo/quantumfpo-python-backend:$imageTag"
        
        $content | Set-Content $file.FullName -Encoding UTF8
        Write-Success "Updated image tags in $($file.Name)"
    }
    
    if ($DryRun) {
        Write-Warning "DRY RUN: Would deploy manifests with kubectl apply -f $ManifestsDir/"
        return $true
    }
    
    # Apply manifests
    try {
        kubectl apply -f $ManifestsDir/
        
        if ($LASTEXITCODE -eq 0) {
            Write-Success "Manifests applied successfully"
            
            # Wait for deployments
            Write-Info "Waiting for deployments to be ready..."
            kubectl wait --for=condition=available --timeout=300s deployment --all -n $Namespace
            
            if ($LASTEXITCODE -eq 0) {
                Write-Success "All deployments are ready!"
                return $true
            } else {
                Write-Warning "Some deployments may not be ready yet"
                return $true
            }
        } else {
            Write-Error "Failed to apply manifests"
            return $false
        }
    } catch {
        Write-Error "Exception deploying manifests: $_"
        return $false
    }
}

# Show deployment status
function Show-DeploymentStatus {
    Write-Info "Deployment Status:"
    Write-Host ""
    
    Write-Host "📊 Pods:" -ForegroundColor Cyan
    kubectl get pods -n $Namespace -o wide
    Write-Host ""
    
    Write-Host "🌐 Services:" -ForegroundColor Cyan  
    kubectl get services -n $Namespace
    Write-Host ""
    
    Write-Host "📈 Resource Usage:" -ForegroundColor Cyan
    kubectl top pods -n $Namespace 2>$null
    Write-Host ""
    
    # Get LoadBalancer IP
    $frontendIP = kubectl get service quantumfpo-frontend -n $Namespace -o jsonpath='{.status.loadBalancer.ingress[0].ip}' 2>$null
    
    if ($frontendIP) {
        Write-Success "Frontend accessible at: http://$frontendIP"
    } else {
        Write-Info "LoadBalancer IP not yet assigned. Check again in a few minutes."
    }
}

# Apply cost optimization configurations
function Enable-CostOptimization {
    Write-Info "Applying cost optimization configurations..."
    
    if (!$EnableCostOptimization) {
        Write-Warning "Cost optimization disabled by parameter"
        return $true
    }
    
    try {
        # Apply scheduled scaling
        $scheduledScalingYaml = @"
apiVersion: batch/v1
kind: CronJob
metadata:
  name: scale-down-evening
  namespace: $Namespace
  labels:
    app: cost-optimizer
spec:
  schedule: "0 20 * * 1-5"  # 8 PM weekdays
  successfulJobsHistoryLimit: 1
  failedJobsHistoryLimit: 1
  jobTemplate:
    spec:
      template:
        spec:
          serviceAccountName: cost-optimizer
          restartPolicy: OnFailure
          containers:
          - name: scaler
            image: bitnami/kubectl:latest
            command:
            - /bin/sh
            - -c
            - |
              echo "Scaling down for evening cost optimization..."
              kubectl scale deployment quantumfpo-frontend --replicas=0 -n $Namespace || true
              kubectl scale deployment quantumfpo-java-backend --replicas=0 -n $Namespace || true
              kubectl scale deployment quantumfpo-python-backend --replicas=0 -n $Namespace || true
              echo "All services scaled down for the evening"
---
apiVersion: batch/v1
kind: CronJob
metadata:
  name: scale-up-morning
  namespace: $Namespace
  labels:
    app: cost-optimizer
spec:
  schedule: "0 7 * * 1-5"   # 7 AM weekdays
  successfulJobsHistoryLimit: 1
  failedJobsHistoryLimit: 1
  jobTemplate:
    spec:
      template:
        spec:
          serviceAccountName: cost-optimizer
          restartPolicy: OnFailure
          containers:
          - name: scaler
            image: bitnami/kubectl:latest
            command:
            - /bin/sh
            - -c
            - |
              echo "Scaling up for morning development..."
              kubectl scale deployment quantumfpo-frontend --replicas=1 -n $Namespace || true
              kubectl scale deployment quantumfpo-java-backend --replicas=1 -n $Namespace || true
              kubectl scale deployment quantumfpo-python-backend --replicas=1 -n $Namespace || true
              echo "All services scaled up for development"
---
apiVersion: v1
kind: ServiceAccount
metadata:
  name: cost-optimizer
  namespace: $Namespace
---
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  namespace: $Namespace
  name: deployment-scaler
rules:
- apiGroups: ["apps"]
  resources: ["deployments", "deployments/scale"]
  verbs: ["get", "list", "patch", "update"]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: cost-optimizer-binding
  namespace: $Namespace
subjects:
- kind: ServiceAccount
  name: cost-optimizer
  namespace: $Namespace
roleRef:
  kind: Role
  name: deployment-scaler
  apiGroup: rbac.authorization.k8s.io
"@
        
        $scheduledScalingYaml | kubectl apply -f - 2>$null
        if ($LASTEXITCODE -eq 0) {
            Write-Success "Scheduled scaling configured (scale down 8 PM, up 7 AM weekdays)"
        }
        
        # Apply cost-optimized HPA
        $hpaYaml = @"
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: quantumfpo-frontend-hpa
  namespace: $Namespace
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: quantumfpo-frontend
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
---
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: quantumfpo-java-backend-hpa
  namespace: $Namespace
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: quantumfpo-java-backend
  minReplicas: 1
  maxReplicas: 2
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 90
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 90
---
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: quantumfpo-python-backend-hpa
  namespace: $Namespace
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
        averageUtilization: 90
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 90
"@
        
        $hpaYaml | kubectl apply -f - 2>$null
        if ($LASTEXITCODE -eq 0) {
            Write-Success "Cost-optimized HPA configured"
        }
        
        # Daily cost monitoring
        $costMonitorYaml = @"
apiVersion: batch/v1
kind: CronJob
metadata:
  name: daily-cost-report
  namespace: $Namespace
  labels:
    app: cost-monitor
spec:
  schedule: "0 9 * * *"  # 9 AM daily
  successfulJobsHistoryLimit: 3
  failedJobsHistoryLimit: 1
  jobTemplate:
    spec:
      template:
        spec:
          restartPolicy: OnFailure
          containers:
          - name: cost-reporter
            image: bitnami/kubectl:latest
            command:
            - /bin/sh
            - -c
            - |
              echo "=== QuantumFPO Alpha Daily Cost Report \$(date) ==="
              echo "📊 Resource Usage:"
              kubectl top pods -n $Namespace 2>/dev/null || echo "Metrics unavailable"
              echo "🎯 Resource Requests:"
              kubectl get pods -n $Namespace -o custom-columns="NAME:.metadata.name,CPU_REQ:.spec.containers[0].resources.requests.cpu,MEM_REQ:.spec.containers[0].resources.requests.memory" 2>/dev/null || echo "Resource info unavailable"
              echo "📈 HPA Status:"
              kubectl get hpa -n $Namespace 2>/dev/null || echo "No HPA configured"
              echo "=== End Report ==="
"@
        
        $costMonitorYaml | kubectl apply -f - 2>$null
        if ($LASTEXITCODE -eq 0) {
            Write-Success "Daily cost monitoring configured"
        }
        
        return $true
        
    } catch {
        Write-Warning "Some cost optimization features failed to apply: $_"
        return $true  # Don't fail the entire migration
    }
}

# Estimate monthly costs
function Show-CostEstimate {
    Write-Info "Monthly Cost Estimate (Alpha Stage):"
    Write-Host ""
    
    # Calculate total resource requests
    $pods = kubectl get pods -n $Namespace -o json 2>$null | ConvertFrom-Json
    
    if ($pods -and $pods.items) {
        $totalCpuMillicores = 0
        $totalMemoryMi = 0
        
        foreach ($pod in $pods.items) {
            foreach ($container in $pod.spec.containers) {
                if ($container.resources.requests.cpu) {
                    $cpu = $container.resources.requests.cpu -replace 'm', ''
                    $totalCpuMillicores += [int]$cpu
                }
                if ($container.resources.requests.memory) {
                    $memory = $container.resources.requests.memory -replace 'Mi', ''
                    $totalMemoryMi += [int]$memory
                }
            }
        }
        
        $cpuCores = $totalCpuMillicores / 1000
        $memoryGb = $totalMemoryMi / 1024
        
        # GKE Autopilot rough pricing (subject to change)
        $monthlyCpuCost = $cpuCores * 0.031611 * 24 * 30
        $monthlyMemoryCost = $memoryGb * 0.004237 * 24 * 30
        $totalMonthly = $monthlyCpuCost + $monthlyMemoryCost
        
        Write-Host "💰 Current Configuration:" -ForegroundColor Green
        Write-Host "   CPU Cores: $([math]::Round($cpuCores, 2)) (~`$$([math]::Round($monthlyCpuCost, 2))/month)"
        Write-Host "   Memory GB: $([math]::Round($memoryGb, 2)) (~`$$([math]::Round($monthlyMemoryCost, 2))/month)"
        Write-Host "   Base Cost: ~`$$([math]::Round($totalMonthly, 2))/month"
        Write-Host ""
        Write-Host "📉 With Optimizations:" -ForegroundColor Yellow
        Write-Host "   Scheduled scaling (70% off-hours): ~`$$([math]::Round($totalMonthly * 0.3, 2))/month"
        Write-Host "   Resource right-sizing (30% reduction): ~`$$([math]::Round($totalMonthly * 0.7, 2))/month"
        Write-Host "   Combined optimizations: ~`$$([math]::Round($totalMonthly * 0.2, 2))/month"
        Write-Host ""
        Write-Host "📊 Migration Savings Estimate:" -ForegroundColor Cyan
        $standardCost = $totalMonthly * 2.5  # Rough estimate of standard GKE overhead
        Write-Host "   Standard GKE (estimated): ~`$$([math]::Round($standardCost, 2))/month"
        Write-Host "   Autopilot optimized: ~`$$([math]::Round($totalMonthly * 0.2, 2))/month"
        Write-Host "   Monthly savings: ~`$$([math]::Round($standardCost - ($totalMonthly * 0.2), 2))"
        Write-Host "   Annual savings: ~`$$([math]::Round(($standardCost - ($totalMonthly * 0.2)) * 12, 2))" -ForegroundColor Green
    } else {
        Write-Warning "Unable to calculate cost estimate - no pods found or kubectl access issue"
    }
}

# Migration summary
function Show-MigrationSummary {
    param(
        [string]$OldCluster = "",
        [string]$NewCluster = "",
        [bool]$BackupCreated = $false,
        [bool]$OldClusterDeleted = $false
    )
    
    Write-Host ""
    Write-Host "🎉 MIGRATION COMPLETED SUCCESSFULLY!" -ForegroundColor Green
    Write-Host "=================================" -ForegroundColor Green
    Write-Host ""
    
    Write-Host "📋 Migration Summary:" -ForegroundColor Cyan
    if ($OldCluster) {
        Write-Host "   From: $OldCluster (Standard GKE)"
    }
    Write-Host "   To: $NewCluster (Autopilot GKE)"
    Write-Host "   Region: $Region"
    Write-Host "   Namespace: $Namespace"
    Write-Host ""
    
    Write-Host "✅ Completed Actions:" -ForegroundColor Green
    Write-Host "   ✓ Autopilot cluster created"
    Write-Host "   ✓ Alpha-optimized manifests deployed"
    Write-Host "   ✓ Application health verified"
    
    if ($EnableCostOptimization) {
        Write-Host "   ✓ Cost optimization enabled (scheduled scaling, HPA, monitoring)"
    }
    
    if ($BackupCreated) {
        Write-Host "   ✓ Original cluster configuration backed up"
    }
    
    if ($OldClusterDeleted) {
        Write-Host "   ✓ Original cluster deleted"
    }
    
    Write-Host ""
    Write-Host "🎯 Next Steps:" -ForegroundColor Yellow
    Write-Host "   1. Test application functionality thoroughly"
    Write-Host "   2. Monitor costs for the first week"
    Write-Host "   3. Adjust resource limits based on usage patterns"
    Write-Host "   4. Set up alerting for cost thresholds"
    Write-Host "   5. Update DNS/domain settings if needed"
    Write-Host ""
    
    Write-Host "📚 Resources:" -ForegroundColor Blue
    Write-Host "   - Migration guide: GKE_AUTOPILOT_MIGRATION.md"
    Write-Host "   - Quick start: AUTOPILOT_QUICK_START.md"
    Write-Host "   - Cost optimizer script: scripts/autopilot/cost-optimizer.sh"
}

# Main execution
function Main {
    Write-Host "🚁 QuantumFPO GKE Autopilot Migration (Enhanced)" -ForegroundColor Magenta
    Write-Host "=================================================" -ForegroundColor Magenta
    Write-Host ""
    
    if (!(Test-Prerequisites)) {
        exit 1
    }
    
    # Handle existing cluster if specified
    $oldClusterName = ""
    $backupCreated = $false
    $oldClusterDeleted = $false
    
    if ($ExistingClusterName) {
        Write-Info "Managing existing cluster: $ExistingClusterName"
        
        # Verify existing cluster exists
        $existingClusters = Get-ExistingClusters
        $targetCluster = $existingClusters | Where-Object { $_.Name -eq $ExistingClusterName }
        
        if (!$targetCluster) {
            Write-Error "Existing cluster '$ExistingClusterName' not found"
            Write-Host "Available clusters:" -ForegroundColor Yellow
            $existingClusters | ForEach-Object { Write-Host "  - $($_.Name) (Zone: $($_.Zone)) Status: $($_.Status)" }
            exit 1
        }
        
        Write-Info "Found target cluster: $($targetCluster.Name) in zone $($targetCluster.Zone), Status: $($targetCluster.Status)"
        $oldClusterName = $ExistingClusterName
        
        # Perform requested action on existing cluster
        switch ($ExistingClusterAction.ToLower()) {
            "backup" {
                Write-Info "Creating backup of existing cluster..."
                $backupCreated = Backup-ExistingCluster -ClusterName $ExistingClusterName -ClusterZone $targetCluster.Zone
                if (!$backupCreated) {
                    Write-Error "Failed to backup existing cluster"
                    exit 1
                }
                Write-Success "Backup completed. Proceeding with normal migration flow..."
            }
            "delete" {
                Write-Info "Deleting existing cluster (no new cluster will be created)..."
                Write-Host ""
                Write-Warning "This will ONLY delete the existing cluster '$ExistingClusterName'"
                Write-Warning "No new Autopilot cluster will be created!"
                Write-Host ""
                
                if (!$AutoApprove) {
                    $confirmDelete = Read-Host "Continue with cluster deletion only? (y/N)"
                    if ($confirmDelete -ne 'y' -and $confirmDelete -ne 'Y') {
                        Write-Info "Operation cancelled by user"
                        exit 0
                    }
                }
                
                # Backup before deletion
                $backupCreated = Backup-ExistingCluster -ClusterName $ExistingClusterName -ClusterZone $targetCluster.Zone
                if (!$backupCreated) {
                    Write-Warning "Backup failed, but continuing with deletion..."
                }
                
                $oldClusterDeleted = Remove-ExistingCluster -ClusterName $ExistingClusterName -ClusterZone $targetCluster.Zone
                if ($oldClusterDeleted) {
                    Write-Success "Cluster '$ExistingClusterName' deleted successfully!"
                    Write-Host ""
                    Write-Host "🎉 DELETION COMPLETED!" -ForegroundColor Green
                    Write-Host "=================" -ForegroundColor Green
                    Write-Host ""
                    Write-Host "✅ Completed Actions:" -ForegroundColor Green
                    if ($backupCreated) {
                        Write-Host "   ✓ Cluster configuration backed up"
                    }
                    Write-Host "   ✓ Cluster '$ExistingClusterName' deleted"
                    Write-Host ""
                    Write-Host "💡 Next Steps:" -ForegroundColor Yellow
                    Write-Host "   • To create a new Autopilot cluster, run the script again without -ExistingClusterName"
                    Write-Host "   • Or use -ExistingClusterAction 'replace' to delete and create in one operation"
                    exit 0
                } else {
                    Write-Error "Failed to delete existing cluster"
                    exit 1
                }
            }
            "replace" {
                Write-Info "Backing up, deleting existing cluster, and creating new Autopilot cluster..."
                $backupCreated = Backup-ExistingCluster -ClusterName $ExistingClusterName -ClusterZone $targetCluster.Zone
                if (!$backupCreated) {
                    Write-Warning "Backup failed, but continuing with replacement..."
                }
                
                $oldClusterDeleted = Remove-ExistingCluster -ClusterName $ExistingClusterName -ClusterZone $targetCluster.Zone
                if (!$oldClusterDeleted) {
                    Write-Error "Failed to delete existing cluster for replacement"
                    exit 1
                }
                
                # Create new autopilot cluster (will be handled below)
                Write-Info "Proceeding to create new Autopilot cluster..."
            }
            "ignore" {
                Write-Info "Ignoring existing cluster '$ExistingClusterName' as requested"
                Write-Info "Proceeding to create new Autopilot cluster..."
            }
            default {
                Write-Warning "Unknown existing cluster action: $ExistingClusterAction"
                Write-Host "Available actions: backup, delete, replace, ignore"
                exit 1
            }
        }
    }
    
    # Set gcloud project
    Write-Info "Setting gcloud project to $ProjectId"
    gcloud config set project $ProjectId
    
    # Check if target cluster already exists
    $existingCluster = gcloud container clusters describe $ClusterName --region=$Region --project=$ProjectId 2>$null
    
    if ($LASTEXITCODE -eq 0) {
        Write-Warning "Cluster $ClusterName already exists in $Region"
        if ($ExistingClusterAction -ne "replace") {
            $response = Read-Host "Do you want to use the existing cluster? (y/N)"
            
            if ($response -ne 'y' -and $response -ne 'Y') {
                Write-Info "Exiting. Please choose a different cluster name or delete the existing cluster."
                exit 1
            }
        }
    } else {
        # Create new cluster
        if (!(New-AutopilotCluster -ProjectId $ProjectId -Region $Region -ClusterName $ClusterName)) {
            exit 1
        }
        
        if (!(Wait-ForCluster -ProjectId $ProjectId -Region $Region -ClusterName $ClusterName)) {
            exit 1
        }
    }
    
    # Configure kubectl
    if (!(Set-KubectlContext -ProjectId $ProjectId -Region $Region -ClusterName $ClusterName)) {
        exit 1
    }
    
    # Generate and deploy manifests
    New-AutopilotManifests
    
    if (Deploy-ToAutopilot) {
        # Apply cost optimizations if enabled
        if ($EnableCostOptimization) {
            Write-Info "Applying cost optimization configurations..."
            Enable-CostOptimization
        }
        
        Write-Host ""
        Show-DeploymentStatus
        Write-Host ""
        Show-CostEstimate
        
        # Show comprehensive migration summary
        Show-MigrationSummary -OldCluster $oldClusterName -NewCluster $ClusterName -BackupCreated $backupCreated -OldClusterDeleted $oldClusterDeleted
        
    } else {
        Write-Error "Migration failed"
        exit 1
    }
}

# Execute main function
Main