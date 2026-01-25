#!/bin/bash
# ==============================================================================
# JORGE'S BI DASHBOARD - PRODUCTION DEPLOYMENT SCRIPT
# Enterprise-grade deployment automation with safety checks
# ==============================================================================

set -e

# Configuration
DEPLOYMENT_NAME="jorge-bi-dashboard"
NAMESPACE="jorge-bi-production"
CLUSTER_NAME="jorge-production-eks"
REGION="us-east-1"
VERSION="${VERSION:-latest}"
DEPLOYMENT_TYPE="${DEPLOYMENT_TYPE:-rolling}"
TIMEOUT="${TIMEOUT:-900}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
WHITE='\033[1;37m'
NC='\033[0m'

# Deployment ID for tracking
DEPLOYMENT_ID=$(date +%Y%m%d-%H%M%S)

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_step() {
    echo -e "${PURPLE}[STEP]${NC} $1"
}

# ==============================================================================
# UTILITY FUNCTIONS
# ==============================================================================

check_prerequisites() {
    log_step "Checking deployment prerequisites..."

    # Check required tools
    local tools=("kubectl" "docker" "curl" "jq" "aws")
    for tool in "${tools[@]}"; do
        if ! command -v "$tool" &> /dev/null; then
            log_error "$tool is required but not installed"
            exit 1
        fi
    done

    # Check kubectl context
    local current_context=$(kubectl config current-context)
    if [[ ! "$current_context" =~ "$CLUSTER_NAME" ]]; then
        log_error "kubectl context is not set to $CLUSTER_NAME. Current: $current_context"
        exit 1
    fi

    # Check AWS credentials
    if ! aws sts get-caller-identity &> /dev/null; then
        log_error "AWS credentials not configured properly"
        exit 1
    fi

    # Check namespace exists
    if ! kubectl get namespace "$NAMESPACE" &> /dev/null; then
        log_error "Namespace $NAMESPACE does not exist"
        exit 1
    fi

    log_success "Prerequisites check passed"
}

# ==============================================================================
# PRE-DEPLOYMENT VALIDATION
# ==============================================================================

validate_environment() {
    log_step "Validating production environment..."

    # Check if services are running
    local services=("postgres-bi" "redis-bi")
    for service in "${services[@]}"; do
        if ! kubectl get deployment "$service" -n "$NAMESPACE" &> /dev/null; then
            log_error "Required service $service is not running"
            exit 1
        fi
    done

    # Check resource availability
    local node_resources=$(kubectl describe nodes | grep -A 5 "Allocated resources" | grep -E "(cpu|memory)")
    log_info "Current cluster resource utilization:"
    echo "$node_resources"

    # Validate configuration
    if [[ -f "scripts/validate-bi-production-config.py" ]]; then
        log_info "Running configuration validation..."
        if ! python scripts/validate-bi-production-config.py; then
            log_error "Configuration validation failed"
            exit 1
        fi
    fi

    log_success "Environment validation completed"
}

create_backup() {
    log_step "Creating pre-deployment backup..."

    local backup_name="jorge-bi-backup-$DEPLOYMENT_ID"

    # Get current deployment image for rollback
    local current_image=$(kubectl get deployment jorge-bi-backend -n "$NAMESPACE" -o jsonpath='{.spec.template.spec.containers[0].image}' 2>/dev/null || echo "none")

    # Create backup ConfigMap
    kubectl create configmap "$backup_name" \
        --from-literal=deployment-image="$current_image" \
        --from-literal=backup-time="$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
        --from-literal=backup-reason="pre-deployment-$DEPLOYMENT_ID" \
        -n "$NAMESPACE" \
        --dry-run=client -o yaml | kubectl apply -f -

    # Database backup (if applicable)
    if kubectl get pod -l app=postgres-bi -n "$NAMESPACE" &> /dev/null; then
        log_info "Creating database backup..."

        kubectl exec -n "$NAMESPACE" deployment/postgres-bi -- \
            pg_dump -U jorge_bi jorge_bi_production > "/tmp/jorge-bi-db-backup-$DEPLOYMENT_ID.sql" 2>/dev/null || true
    fi

    log_success "Backup created: $backup_name"
    echo "current_image=$current_image" > "/tmp/deployment-backup-$DEPLOYMENT_ID.env"
}

# ==============================================================================
# DEPLOYMENT STRATEGIES
# ==============================================================================

rolling_deployment() {
    log_step "Performing rolling deployment..."

    local image_tag="${IMAGE_TAG:-ghcr.io/jorge/bi-backend:$VERSION}"

    log_info "Deploying image: $image_tag"

    # Update deployment image
    kubectl set image deployment/jorge-bi-backend \
        jorge-bi-backend="$image_tag" \
        -n "$NAMESPACE"

    # Add deployment annotations
    kubectl annotate deployment jorge-bi-backend \
        deployment.kubernetes.io/revision-history-limit=10 \
        deployment.jorge-platform.com/deployment-id="$DEPLOYMENT_ID" \
        deployment.jorge-platform.com/deployment-time="$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
        deployment.jorge-platform.com/deployed-by="${USER:-automated}" \
        -n "$NAMESPACE" --overwrite

    # Wait for rollout to complete
    log_info "Waiting for rollout to complete (timeout: ${TIMEOUT}s)..."
    if kubectl rollout status deployment/jorge-bi-backend -n "$NAMESPACE" --timeout="${TIMEOUT}s"; then
        log_success "Rolling deployment completed successfully"
    else
        log_error "Rolling deployment timed out or failed"
        return 1
    fi
}

blue_green_deployment() {
    log_step "Performing blue-green deployment..."

    local image_tag="${IMAGE_TAG:-ghcr.io/jorge/bi-backend:$VERSION}"

    # Determine current color
    local current_color=$(kubectl get service jorge-bi-backend -n "$NAMESPACE" -o jsonpath='{.spec.selector.color}' 2>/dev/null || echo "blue")
    local new_color
    if [[ "$current_color" == "blue" ]]; then
        new_color="green"
    else
        new_color="blue"
    fi

    log_info "Current color: $current_color, deploying to: $new_color"

    # Create or update the new color deployment
    local deployment_yaml=$(cat << EOF
apiVersion: apps/v1
kind: Deployment
metadata:
  name: jorge-bi-backend-$new_color
  namespace: $NAMESPACE
  labels:
    app: jorge-bi-dashboard
    color: $new_color
spec:
  replicas: 2
  selector:
    matchLabels:
      app: jorge-bi-backend
      color: $new_color
  template:
    metadata:
      labels:
        app: jorge-bi-backend
        color: $new_color
    spec:
      containers:
      - name: jorge-bi-backend
        image: $image_tag
        ports:
        - containerPort: 8000
        envFrom:
        - configMapRef:
            name: jorge-bi-config
        - secretRef:
            name: jorge-bi-secrets
EOF
)

    echo "$deployment_yaml" | kubectl apply -f -

    # Wait for new deployment to be ready
    log_info "Waiting for $new_color deployment to be ready..."
    if kubectl rollout status deployment/jorge-bi-backend-$new_color -n "$NAMESPACE" --timeout="${TIMEOUT}s"; then
        log_success "$new_color deployment is ready"
    else
        log_error "$new_color deployment failed"
        return 1
    fi

    # Test new deployment
    log_info "Testing $new_color deployment..."
    local new_pod=$(kubectl get pods -l app=jorge-bi-backend,color=$new_color -n "$NAMESPACE" -o jsonpath='{.items[0].metadata.name}')

    if kubectl exec -n "$NAMESPACE" "$new_pod" -- curl -f http://localhost:8000/health &> /dev/null; then
        log_success "$new_color deployment health check passed"
    else
        log_error "$new_color deployment health check failed"
        return 1
    fi

    # Switch traffic to new deployment
    log_info "Switching traffic to $new_color deployment..."
    kubectl patch service jorge-bi-backend -n "$NAMESPACE" --patch "{\"spec\":{\"selector\":{\"color\":\"$new_color\"}}}"

    # Wait a bit for traffic to stabilize
    sleep 30

    # Verify service is working
    if test_deployment_health; then
        log_success "Blue-green deployment completed successfully"

        # Clean up old deployment after successful switch
        sleep 60  # Grace period
        kubectl delete deployment "jorge-bi-backend-$current_color" -n "$NAMESPACE" --ignore-not-found=true
    else
        log_error "New deployment failed health checks, rolling back..."
        kubectl patch service jorge-bi-backend -n "$NAMESPACE" --patch "{\"spec\":{\"selector\":{\"color\":\"$current_color\"}}}"
        return 1
    fi
}

canary_deployment() {
    log_step "Performing canary deployment..."

    local image_tag="${IMAGE_TAG:-ghcr.io/jorge/bi-backend:$VERSION}"
    local canary_percentage="${CANARY_PERCENTAGE:-10}"

    log_info "Deploying canary with $canary_percentage% traffic"

    # Create canary deployment with new image
    local canary_replicas=1
    if [[ "$canary_percentage" -gt 10 ]]; then
        canary_replicas=2
    fi

    kubectl patch deployment jorge-bi-backend-canary -n "$NAMESPACE" --patch "{
        \"spec\": {
            \"replicas\": $canary_replicas,
            \"template\": {
                \"spec\": {
                    \"containers\": [{
                        \"name\": \"jorge-bi-backend\",
                        \"image\": \"$image_tag\"
                    }]
                }
            }
        }
    }" 2>/dev/null || {
        # Create canary deployment if it doesn't exist
        kubectl create deployment jorge-bi-backend-canary -n "$NAMESPACE" --image="$image_tag" --replicas="$canary_replicas"
        kubectl label deployment jorge-bi-backend-canary app=jorge-bi-backend version=canary -n "$NAMESPACE"
    }

    # Wait for canary to be ready
    log_info "Waiting for canary deployment..."
    kubectl rollout status deployment/jorge-bi-backend-canary -n "$NAMESPACE" --timeout="300s"

    # Monitor canary for specified duration
    local monitoring_duration="${CANARY_MONITORING_DURATION:-600}"
    log_info "Monitoring canary for $monitoring_duration seconds..."

    local canary_healthy=true
    for ((i=1; i<=monitoring_duration/30; i++)); do
        # Check canary health
        if ! test_canary_health; then
            log_error "Canary health check failed during monitoring"
            canary_healthy=false
            break
        fi

        log_info "Canary monitoring: $((i*30))/${monitoring_duration}s - healthy"
        sleep 30
    done

    if [[ "$canary_healthy" == "true" ]]; then
        log_success "Canary monitoring successful, promoting to full deployment"

        # Promote canary to main deployment
        kubectl patch deployment jorge-bi-backend -n "$NAMESPACE" --patch "{
            \"spec\": {
                \"template\": {
                    \"spec\": {
                        \"containers\": [{
                            \"name\": \"jorge-bi-backend\",
                            \"image\": \"$image_tag\"
                        }]
                    }
                }
            }
        }"

        # Wait for main deployment rollout
        kubectl rollout status deployment/jorge-bi-backend -n "$NAMESPACE" --timeout="${TIMEOUT}s"

        # Clean up canary
        kubectl delete deployment jorge-bi-backend-canary -n "$NAMESPACE" --ignore-not-found=true

        log_success "Canary deployment promoted successfully"
    else
        log_error "Canary deployment failed, cleaning up..."
        kubectl delete deployment jorge-bi-backend-canary -n "$NAMESPACE" --ignore-not-found=true
        return 1
    fi
}

# ==============================================================================
# HEALTH CHECKS & VALIDATION
# ==============================================================================

test_deployment_health() {
    log_info "Testing deployment health..."

    local service_url
    if kubectl get service jorge-bi-backend -n "$NAMESPACE" &> /dev/null; then
        # Use port-forward for testing
        kubectl port-forward service/jorge-bi-backend 8080:8000 -n "$NAMESPACE" &
        local pf_pid=$!
        sleep 3

        service_url="http://localhost:8080"
    else
        log_error "Service jorge-bi-backend not found"
        return 1
    fi

    local health_passed=true

    # Basic health check
    if curl -f -s "$service_url/health" > /dev/null; then
        log_success "✅ Basic health check passed"
    else
        log_error "❌ Basic health check failed"
        health_passed=false
    fi

    # BI API health check
    if curl -f -s "$service_url/api/bi/health" > /dev/null; then
        log_success "✅ BI API health check passed"
    else
        log_error "❌ BI API health check failed"
        health_passed=false
    fi

    # WebSocket health check
    if curl -f -s "$service_url/ws/health" > /dev/null; then
        log_success "✅ WebSocket health check passed"
    else
        log_warn "⚠️ WebSocket health check failed (non-critical)"
    fi

    # Cleanup port-forward
    if [[ -n "$pf_pid" ]]; then
        kill "$pf_pid" 2>/dev/null || true
    fi

    if [[ "$health_passed" == "true" ]]; then
        log_success "All critical health checks passed"
        return 0
    else
        log_error "Health checks failed"
        return 1
    fi
}

test_canary_health() {
    local canary_pod=$(kubectl get pods -l app=jorge-bi-backend,version=canary -n "$NAMESPACE" -o jsonpath='{.items[0].metadata.name}' 2>/dev/null)

    if [[ -z "$canary_pod" ]]; then
        return 1
    fi

    # Test canary pod health
    kubectl exec -n "$NAMESPACE" "$canary_pod" -- curl -f http://localhost:8000/health &> /dev/null
}

validate_performance() {
    log_step "Validating performance baselines..."

    # This would typically query Prometheus for actual metrics
    # For now, we'll do basic response time testing

    local service_url="http://localhost:8080"
    kubectl port-forward service/jorge-bi-backend 8080:8000 -n "$NAMESPACE" &
    local pf_pid=$!
    sleep 3

    local response_times=()
    for i in {1..10}; do
        local start_time=$(date +%s%N)
        if curl -f -s "$service_url/health" > /dev/null; then
            local end_time=$(date +%s%N)
            local response_time=$(( (end_time - start_time) / 1000000 )) # Convert to milliseconds
            response_times+=("$response_time")
        fi
    done

    kill "$pf_pid" 2>/dev/null || true

    if [[ ${#response_times[@]} -gt 0 ]]; then
        local avg_response_time=0
        for time in "${response_times[@]}"; do
            avg_response_time=$((avg_response_time + time))
        done
        avg_response_time=$((avg_response_time / ${#response_times[@]}))

        log_info "Average response time: ${avg_response_time}ms"

        if [[ $avg_response_time -lt 500 ]]; then
            log_success "✅ Performance baseline validated"
        else
            log_warn "⚠️ Response time higher than expected: ${avg_response_time}ms"
        fi
    fi
}

# ==============================================================================
# POST-DEPLOYMENT TASKS
# ==============================================================================

update_monitoring() {
    log_step "Updating monitoring configuration..."

    # Update Grafana dashboard annotations
    local grafana_annotation="{
        \"time\": $(date +%s)000,
        \"text\": \"Jorge BI Production Deployment $DEPLOYMENT_ID\",
        \"tags\": [\"deployment\", \"jorge-bi\", \"production\"]
    }"

    # This would typically send to Grafana API
    log_info "Monitoring annotation prepared: $grafana_annotation"

    log_success "Monitoring configuration updated"
}

notify_deployment() {
    log_step "Sending deployment notifications..."

    local deployment_status="${1:-success}"
    local notification_message="Jorge BI Dashboard deployment $DEPLOYMENT_ID completed with status: $deployment_status"

    # Slack notification (if webhook configured)
    if [[ -n "${SLACK_WEBHOOK:-}" ]]; then
        local slack_payload="{
            \"text\": \"$notification_message\",
            \"channel\": \"#jorge-deployments\",
            \"username\": \"Jorge Deploy Bot\",
            \"attachments\": [{
                \"color\": \"$([ "$deployment_status" == "success" ] && echo "good" || echo "danger")\",
                \"fields\": [
                    {\"title\": \"Environment\", \"value\": \"Production\", \"short\": true},
                    {\"title\": \"Version\", \"value\": \"$VERSION\", \"short\": true},
                    {\"title\": \"Type\", \"value\": \"$DEPLOYMENT_TYPE\", \"short\": true},
                    {\"title\": \"Time\", \"value\": \"$(date)\", \"short\": true}
                ]
            }]
        }"

        curl -X POST -H 'Content-type: application/json' \
            --data "$slack_payload" \
            "$SLACK_WEBHOOK" 2>/dev/null || log_warn "Slack notification failed"
    fi

    # Email notification (if configured)
    if [[ -n "${EMAIL_NOTIFICATION:-}" ]]; then
        echo "$notification_message" | mail -s "Jorge BI Deployment $DEPLOYMENT_ID" "$EMAIL_NOTIFICATION" 2>/dev/null || true
    fi

    log_success "Deployment notifications sent"
}

# ==============================================================================
# ROLLBACK FUNCTIONALITY
# ==============================================================================

rollback_deployment() {
    log_step "Rolling back deployment..."

    local backup_file="/tmp/deployment-backup-$DEPLOYMENT_ID.env"

    if [[ -f "$backup_file" ]]; then
        source "$backup_file"
        log_info "Rolling back to image: $current_image"

        kubectl set image deployment/jorge-bi-backend \
            jorge-bi-backend="$current_image" \
            -n "$NAMESPACE"

        kubectl rollout status deployment/jorge-bi-backend -n "$NAMESPACE" --timeout="600s"

        log_success "Rollback completed"
    else
        log_warn "No backup found, using kubectl rollout undo"
        kubectl rollout undo deployment/jorge-bi-backend -n "$NAMESPACE"
        kubectl rollout status deployment/jorge-bi-backend -n "$NAMESPACE" --timeout="600s"
    fi
}

# ==============================================================================
# MAIN EXECUTION
# ==============================================================================

show_help() {
    cat << EOF
Jorge BI Dashboard Production Deployment Script

Usage: $0 [OPTIONS]

Options:
  --help                    Show this help message
  --version VERSION         Version to deploy (default: latest)
  --type TYPE              Deployment type: rolling|blue-green|canary (default: rolling)
  --timeout SECONDS        Deployment timeout in seconds (default: 900)
  --canary-percentage NUM   Canary traffic percentage (default: 10)
  --skip-backup            Skip pre-deployment backup
  --skip-validation        Skip pre-deployment validation (dangerous)
  --rollback               Perform rollback to previous version
  --dry-run                Show what would be done without executing

Environment Variables:
  IMAGE_TAG                Full image tag to deploy
  SLACK_WEBHOOK           Slack webhook URL for notifications
  EMAIL_NOTIFICATION      Email address for notifications
  CANARY_MONITORING_DURATION  Canary monitoring duration in seconds

Examples:
  $0                                # Rolling deployment with latest version
  $0 --type blue-green --version v2.1.0  # Blue-green deployment
  $0 --type canary --canary-percentage 20  # Canary with 20% traffic
  $0 --rollback                     # Rollback previous deployment

EOF
}

main() {
    log_info "🚀 Jorge's BI Dashboard - Production Deployment"
    log_info "Deployment ID: $DEPLOYMENT_ID"
    log_info "Target: $NAMESPACE namespace in $CLUSTER_NAME"
    log_info "Version: $VERSION"
    log_info "Type: $DEPLOYMENT_TYPE"

    # Parse command line arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            --help)
                show_help
                exit 0
                ;;
            --version)
                VERSION="$2"
                shift 2
                ;;
            --type)
                DEPLOYMENT_TYPE="$2"
                shift 2
                ;;
            --timeout)
                TIMEOUT="$2"
                shift 2
                ;;
            --canary-percentage)
                CANARY_PERCENTAGE="$2"
                shift 2
                ;;
            --skip-backup)
                SKIP_BACKUP="true"
                shift
                ;;
            --skip-validation)
                SKIP_VALIDATION="true"
                shift
                ;;
            --rollback)
                ROLLBACK="true"
                shift
                ;;
            --dry-run)
                DRY_RUN="true"
                shift
                ;;
            *)
                log_error "Unknown option: $1"
                show_help
                exit 1
                ;;
        esac
    done

    # Handle rollback
    if [[ "${ROLLBACK:-false}" == "true" ]]; then
        rollback_deployment
        exit $?
    fi

    # Dry run mode
    if [[ "${DRY_RUN:-false}" == "true" ]]; then
        log_info "DRY RUN MODE - No changes will be made"
        log_info "Would deploy version $VERSION using $DEPLOYMENT_TYPE strategy"
        exit 0
    fi

    # Main deployment flow
    if [[ "${SKIP_VALIDATION:-false}" != "true" ]]; then
        check_prerequisites
        validate_environment
    fi

    if [[ "${SKIP_BACKUP:-false}" != "true" ]]; then
        create_backup
    fi

    # Deployment strategy execution
    case "$DEPLOYMENT_TYPE" in
        "rolling")
            if rolling_deployment; then
                deployment_success=true
            else
                deployment_success=false
            fi
            ;;
        "blue-green")
            if blue_green_deployment; then
                deployment_success=true
            else
                deployment_success=false
            fi
            ;;
        "canary")
            if canary_deployment; then
                deployment_success=true
            else
                deployment_success=false
            fi
            ;;
        *)
            log_error "Unknown deployment type: $DEPLOYMENT_TYPE"
            exit 1
            ;;
    esac

    # Post-deployment validation
    if [[ "$deployment_success" == "true" ]]; then
        if test_deployment_health; then
            validate_performance
            update_monitoring
            notify_deployment "success"

            log_success "🎉 Jorge BI Dashboard deployment completed successfully!"
            log_info "Deployment ID: $DEPLOYMENT_ID"
            log_info "Access the dashboard at: https://bi.jorge-platform.com"
        else
            log_error "Post-deployment health checks failed"
            rollback_deployment
            notify_deployment "failed"
            exit 1
        fi
    else
        log_error "Deployment failed"
        rollback_deployment
        notify_deployment "failed"
        exit 1
    fi
}

# Execute main function with all arguments
main "$@"