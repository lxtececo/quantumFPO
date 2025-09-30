#!/bin/bash

# QuantumFPO Alpha Cost Optimization Script
# This script implements aggressive cost reduction strategies for alpha-stage development

set -e

PROJECT_ID=${PROJECT_ID:-"your-project-id"}
CLUSTER_NAME=${CLUSTER_NAME:-"quantumfpo-autopilot"}
REGION=${REGION:-"us-central1"}
NAMESPACE=${NAMESPACE:-"quantumfpo"}

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

warn() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] WARNING:${NC} $1"
}

error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ERROR:${NC} $1"
}

# Function to check if cluster is in Autopilot mode
check_autopilot() {
    log "Checking if cluster is in Autopilot mode..."
    
    CLUSTER_MODE=$(gcloud container clusters describe $CLUSTER_NAME --region=$REGION --format="value(autopilot.enabled)" 2>/dev/null || echo "false")
    
    if [ "$CLUSTER_MODE" != "True" ]; then
        error "Cluster $CLUSTER_NAME is not in Autopilot mode. Please create an Autopilot cluster first."
        exit 1
    fi
    
    log "✓ Cluster is in Autopilot mode"
}

# Function to optimize resource requests based on actual usage
optimize_resources() {
    log "Analyzing current resource usage..."
    
    # Get current resource usage
    kubectl top pods -n $NAMESPACE --no-headers 2>/dev/null | while read line; do
        POD_NAME=$(echo $line | awk '{print $1}')
        CPU_USAGE=$(echo $line | awk '{print $2}' | sed 's/m//')
        MEMORY_USAGE=$(echo $line | awk '{print $3}' | sed 's/Mi//')
        
        # Get resource requests
        CPU_REQUEST=$(kubectl get pod $POD_NAME -n $NAMESPACE -o jsonpath='{.spec.containers[0].resources.requests.cpu}' | sed 's/m//')
        MEMORY_REQUEST=$(kubectl get pod $POD_NAME -n $NAMESPACE -o jsonpath='{.spec.containers[0].resources.requests.memory}' | sed 's/Mi//')
        
        # Calculate efficiency (usage vs request)
        if [ ! -z "$CPU_REQUEST" ] && [ "$CPU_REQUEST" -gt 0 ]; then
            CPU_EFFICIENCY=$((CPU_USAGE * 100 / CPU_REQUEST))
        else
            CPU_EFFICIENCY=0
        fi
        
        if [ ! -z "$MEMORY_REQUEST" ] && [ "$MEMORY_REQUEST" -gt 0 ]; then
            MEMORY_EFFICIENCY=$((MEMORY_USAGE * 100 / MEMORY_REQUEST))
        else
            MEMORY_EFFICIENCY=0
        fi
        
        log "Pod: $POD_NAME"
        log "  CPU: ${CPU_USAGE}m used / ${CPU_REQUEST}m requested (${CPU_EFFICIENCY}% efficiency)"
        log "  Memory: ${MEMORY_USAGE}Mi used / ${MEMORY_REQUEST}Mi requested (${MEMORY_EFFICIENCY}% efficiency)"
        
        # Suggest optimizations for low efficiency
        if [ "$CPU_EFFICIENCY" -lt 30 ] && [ "$CPU_REQUEST" -gt 100 ]; then
            warn "  Consider reducing CPU request for $POD_NAME (low efficiency: ${CPU_EFFICIENCY}%)"
        fi
        
        if [ "$MEMORY_EFFICIENCY" -lt 40 ] && [ "$MEMORY_REQUEST" -gt 200 ]; then
            warn "  Consider reducing memory request for $POD_NAME (low efficiency: ${MEMORY_EFFICIENCY}%)"
        fi
        
        echo ""
    done
}

# Function to implement scheduled scaling
setup_scheduled_scaling() {
    log "Setting up scheduled scaling for cost optimization..."
    
    cat <<EOF | kubectl apply -f -
apiVersion: batch/v1
kind: CronJob
metadata:
  name: scale-down-evening
  namespace: $NAMESPACE
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
              kubectl scale deployment quantumfpo-frontend --replicas=0 -n $NAMESPACE
              kubectl scale deployment quantumfpo-java-backend --replicas=0 -n $NAMESPACE
              kubectl scale deployment quantumfpo-python-backend --replicas=0 -n $NAMESPACE
              echo "All services scaled down for the evening"
---
apiVersion: batch/v1
kind: CronJob
metadata:
  name: scale-up-morning
  namespace: $NAMESPACE
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
              kubectl scale deployment quantumfpo-frontend --replicas=1 -n $NAMESPACE
              kubectl scale deployment quantumfpo-java-backend --replicas=1 -n $NAMESPACE
              kubectl scale deployment quantumfpo-python-backend --replicas=1 -n $NAMESPACE
              echo "All services scaled up for development"
---
# Service account for the scaling jobs
apiVersion: v1
kind: ServiceAccount
metadata:
  name: cost-optimizer
  namespace: $NAMESPACE
---
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  namespace: $NAMESPACE
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
  namespace: $NAMESPACE
subjects:
- kind: ServiceAccount
  name: cost-optimizer
  namespace: $NAMESPACE
roleRef:
  kind: Role
  name: deployment-scaler
  apiGroup: rbac.authorization.k8s.io
EOF

    log "✓ Scheduled scaling configured (scale down at 8 PM, up at 7 AM weekdays)"
}

# Function to cleanup unused resources
cleanup_resources() {
    log "Cleaning up unused resources..."
    
    # Clean up completed jobs older than 1 day
    COMPLETED_JOBS=$(kubectl get jobs -n $NAMESPACE -o json | jq -r '.items[] | select(.status.completionTime and (now - (.status.completionTime | fromdateiso8601) > 86400)) | .metadata.name' 2>/dev/null || echo "")
    
    if [ ! -z "$COMPLETED_JOBS" ]; then
        echo "$COMPLETED_JOBS" | xargs -r kubectl delete job -n $NAMESPACE
        log "✓ Cleaned up completed jobs"
    fi
    
    # Clean up failed pods
    FAILED_PODS=$(kubectl get pods -n $NAMESPACE --field-selector=status.phase=Failed -o name 2>/dev/null || echo "")
    
    if [ ! -z "$FAILED_PODS" ]; then
        echo "$FAILED_PODS" | xargs -r kubectl delete -n $NAMESPACE
        log "✓ Cleaned up failed pods"
    fi
    
    # Clean up evicted pods  
    EVICTED_PODS=$(kubectl get pods -n $NAMESPACE | grep Evicted | awk '{print $1}' || echo "")
    
    if [ ! -z "$EVICTED_PODS" ]; then
        echo "$EVICTED_PODS" | xargs -r kubectl delete pod -n $NAMESPACE
        log "✓ Cleaned up evicted pods"
    fi
    
    log "✓ Resource cleanup completed"
}

# Function to set up cost monitoring
setup_cost_monitoring() {
    log "Setting up cost monitoring..."
    
    cat <<EOF | kubectl apply -f -
apiVersion: batch/v1
kind: CronJob
metadata:
  name: daily-cost-report
  namespace: $NAMESPACE
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
              echo "=== QuantumFPO Alpha Daily Cost Report $(date) ==="
              echo ""
              
              echo "📊 Current Resource Usage:"
              kubectl top nodes --use-protocol-buffers 2>/dev/null || echo "Node metrics unavailable"
              echo ""
              
              echo "🏠 Pod Resource Usage:"
              kubectl top pods -n $NAMESPACE --use-protocol-buffers 2>/dev/null || echo "Pod metrics unavailable"
              echo ""
              
              echo "🎯 Resource Requests vs Usage:"
              kubectl get pods -n $NAMESPACE -o custom-columns="NAME:.metadata.name,CPU_REQ:.spec.containers[0].resources.requests.cpu,MEM_REQ:.spec.containers[0].resources.requests.memory,CPU_LIM:.spec.containers[0].resources.limits.cpu,MEM_LIM:.spec.containers[0].resources.limits.memory" 2>/dev/null || echo "Resource info unavailable"
              echo ""
              
              echo "📈 HPA Status:"
              kubectl get hpa -n $NAMESPACE 2>/dev/null || echo "No HPA configured"
              echo ""
              
              echo "💾 Persistent Volumes:"
              kubectl get pvc -n $NAMESPACE 2>/dev/null || echo "No PVC found"
              echo ""
              
              echo "=== End of Report ==="
EOF

    log "✓ Daily cost monitoring configured"
}

# Function to apply alpha-optimized resource limits
apply_alpha_limits() {
    log "Applying alpha-stage resource optimizations..."
    
    # Patch deployments with minimal resource requirements
    kubectl patch deployment quantumfpo-frontend -n $NAMESPACE -p '{
      "spec": {
        "template": {
          "spec": {
            "containers": [
              {
                "name": "frontend",
                "resources": {
                  "requests": {
                    "memory": "64Mi",
                    "cpu": "50m",
                    "ephemeral-storage": "512Mi"
                  },
                  "limits": {
                    "memory": "128Mi", 
                    "cpu": "100m",
                    "ephemeral-storage": "1Gi"
                  }
                }
              }
            ]
          }
        }
      }
    }' 2>/dev/null || warn "Failed to patch frontend resources"
    
    kubectl patch deployment quantumfpo-java-backend -n $NAMESPACE -p '{
      "spec": {
        "template": {
          "spec": {
            "containers": [
              {
                "name": "java-backend",
                "resources": {
                  "requests": {
                    "memory": "400Mi",
                    "cpu": "125m", 
                    "ephemeral-storage": "1Gi"
                  },
                  "limits": {
                    "memory": "768Mi",
                    "cpu": "500m",
                    "ephemeral-storage": "2Gi"
                  }
                }
              }
            ]
          }
        }
      }
    }' 2>/dev/null || warn "Failed to patch java-backend resources"
    
    kubectl patch deployment quantumfpo-python-backend -n $NAMESPACE -p '{
      "spec": {
        "template": {
          "spec": {
            "containers": [
              {
                "name": "python-backend", 
                "resources": {
                  "requests": {
                    "memory": "256Mi",
                    "cpu": "125m",
                    "ephemeral-storage": "1Gi"
                  },
                  "limits": {
                    "memory": "512Mi",
                    "cpu": "250m", 
                    "ephemeral-storage": "2Gi"
                  }
                }
              }
            ]
          }
        }
      }
    }' 2>/dev/null || warn "Failed to patch python-backend resources"
    
    log "✓ Alpha-stage resource limits applied"
}

# Function to configure aggressive HPA
setup_alpha_hpa() {
    log "Configuring cost-optimized HPA..."
    
    cat <<EOF | kubectl apply -f -
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: quantumfpo-frontend-hpa
  namespace: $NAMESPACE
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: quantumfpo-frontend
  minReplicas: 1
  maxReplicas: 2  # Very limited for alpha
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 85  # High threshold for cost
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 85
  behavior:
    scaleDown:
      stabilizationWindowSeconds: 600  # Very slow scale down
      policies:
      - type: Percent
        value: 25
        periodSeconds: 120
    scaleUp:
      stabilizationWindowSeconds: 120
      policies:
      - type: Percent
        value: 50
        periodSeconds: 60
---
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: quantumfpo-java-backend-hpa
  namespace: $NAMESPACE
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
  namespace: $NAMESPACE
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
EOF

    log "✓ Cost-optimized HPA configured"
}

# Function to display cost summary
show_cost_summary() {
    log "Current cost optimization status:"
    echo ""
    
    echo "🎯 Resource Efficiency:"
    kubectl top pods -n $NAMESPACE 2>/dev/null || echo "  Metrics unavailable"
    echo ""
    
    echo "📊 Current Replicas:"
    kubectl get deployments -n $NAMESPACE -o custom-columns="NAME:.metadata.name,REPLICAS:.spec.replicas,AVAILABLE:.status.availableReplicas" 2>/dev/null
    echo ""
    
    echo "🔄 HPA Status:"
    kubectl get hpa -n $NAMESPACE 2>/dev/null || echo "  No HPA found"
    echo ""
    
    echo "⏰ Scheduled Jobs:"
    kubectl get cronjobs -n $NAMESPACE 2>/dev/null || echo "  No scheduled jobs found"
    echo ""
    
    echo "💰 Estimated Monthly Cost:"
    # Calculate rough estimate based on current resource requests
    TOTAL_CPU_MILLICORES=$(kubectl get pods -n $NAMESPACE -o json | jq -r '.items[].spec.containers[].resources.requests.cpu' 2>/dev/null | sed 's/m//' | awk '{sum += $1} END {print sum}' || echo 0)
    TOTAL_MEMORY_MI=$(kubectl get pods -n $NAMESPACE -o json | jq -r '.items[].spec.containers[].resources.requests.memory' 2>/dev/null | sed 's/Mi//' | awk '{sum += $1} END {print sum}' || echo 0)
    
    CPU_CORES=$(echo "scale=2; $TOTAL_CPU_MILLICORES / 1000" | bc 2>/dev/null || echo 0)
    MEMORY_GB=$(echo "scale=2; $TOTAL_MEMORY_MI / 1024" | bc 2>/dev/null || echo 0)
    
    # Rough GKE Autopilot pricing (subject to change)
    MONTHLY_CPU_COST=$(echo "scale=2; $CPU_CORES * 0.031611 * 24 * 30" | bc 2>/dev/null || echo 0)
    MONTHLY_MEMORY_COST=$(echo "scale=2; $MEMORY_GB * 0.004237 * 24 * 30" | bc 2>/dev/null || echo 0)
    TOTAL_MONTHLY=$(echo "scale=2; $MONTHLY_CPU_COST + $MONTHLY_MEMORY_COST" | bc 2>/dev/null || echo 0)
    
    echo "  CPU Cores: $CPU_CORES (~\$${MONTHLY_CPU_COST}/month)"
    echo "  Memory GB: $MEMORY_GB (~\$${MONTHLY_MEMORY_COST}/month)"
    echo "  Estimated Total: ~\$${TOTAL_MONTHLY}/month (without scheduled scaling)"
    echo "  With 70% off-hours scaling: ~\$$(echo "scale=2; $TOTAL_MONTHLY * 0.3" | bc 2>/dev/null)/month"
}

# Main execution
main() {
    log "Starting QuantumFPO Alpha Cost Optimization"
    
    # Check prerequisites
    if ! command -v kubectl &> /dev/null; then
        error "kubectl is not installed"
        exit 1
    fi
    
    if ! command -v gcloud &> /dev/null; then
        error "gcloud CLI is not installed"
        exit 1
    fi
    
    # Verify cluster access
    if ! kubectl cluster-info &> /dev/null; then
        error "Unable to connect to Kubernetes cluster"
        exit 1
    fi
    
    check_autopilot
    
    case "${1:-all}" in
        "analyze")
            optimize_resources
            ;;
        "scale")
            setup_scheduled_scaling
            ;;
        "cleanup")
            cleanup_resources
            ;;
        "monitor")
            setup_cost_monitoring
            ;;
        "limits")
            apply_alpha_limits
            ;;
        "hpa")
            setup_alpha_hpa
            ;;
        "summary")
            show_cost_summary
            ;;
        "all")
            optimize_resources
            apply_alpha_limits
            setup_alpha_hpa
            setup_scheduled_scaling
            setup_cost_monitoring
            cleanup_resources
            show_cost_summary
            ;;
        *)
            echo "Usage: $0 {analyze|scale|cleanup|monitor|limits|hpa|summary|all}"
            echo ""
            echo "Commands:"
            echo "  analyze  - Analyze current resource usage and efficiency"
            echo "  scale    - Set up scheduled scaling for off-hours"
            echo "  cleanup  - Clean up unused resources"
            echo "  monitor  - Set up cost monitoring and reporting"
            echo "  limits   - Apply alpha-stage resource limits"
            echo "  hpa      - Configure cost-optimized auto-scaling"
            echo "  summary  - Show current cost optimization status"
            echo "  all      - Execute all optimization steps"
            exit 1
            ;;
    esac
    
    log "Cost optimization completed successfully!"
}

# Execute main function
main "$@"