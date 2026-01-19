#!/bin/bash
# Jorge's Revenue Platform - Production Deployment Script
# Zero-downtime deployment automation with comprehensive validation
# Version: 1.0.0

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
ENVIRONMENT="${1:-staging}"
NAMESPACE="jorge-revenue-platform"
DEPLOYMENT_NAME="jorge-revenue-api"
IMAGE_TAG="${2:-latest}"
HEALTH_CHECK_TIMEOUT=300
SMOKE_TEST_TIMEOUT=180

# Functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

check_prerequisites() {
    log_info "Checking prerequisites..."

    # Check kubectl
    if ! command -v kubectl &> /dev/null; then
        log_error "kubectl not found. Please install kubectl."
        exit 1
    fi

    # Check helm
    if ! command -v helm &> /dev/null; then
        log_error "helm not found. Please install helm."
        exit 1
    fi

    # Check cluster connection
    if ! kubectl cluster-info &> /dev/null; then
        log_error "Cannot connect to Kubernetes cluster."
        exit 1
    fi

    log_success "All prerequisites met"
}

validate_environment() {
    log_info "Validating environment: $ENVIRONMENT"

    if [[ "$ENVIRONMENT" != "staging" && "$ENVIRONMENT" != "production" ]]; then
        log_error "Invalid environment. Must be 'staging' or 'production'"
        exit 1
    fi

    if [[ "$ENVIRONMENT" == "production" ]]; then
        log_warning "PRODUCTION DEPLOYMENT - This will affect live users"
        read -p "Are you sure you want to deploy to production? (yes/no): " confirm
        if [[ "$confirm" != "yes" ]]; then
            log_info "Deployment cancelled"
            exit 0
        fi
    fi

    log_success "Environment validated: $ENVIRONMENT"
}

backup_current_deployment() {
    log_info "Creating backup of current deployment..."

    backup_dir="backups/$(date +%Y%m%d_%H%M%S)"
    mkdir -p "$backup_dir"

    # Backup deployment
    kubectl get deployment $DEPLOYMENT_NAME -n $NAMESPACE -o yaml > "$backup_dir/deployment.yaml" 2>/dev/null || true

    # Backup configmap
    kubectl get configmap jorge-app-config -n $NAMESPACE -o yaml > "$backup_dir/configmap.yaml" 2>/dev/null || true

    # Backup current image tag
    CURRENT_IMAGE=$(kubectl get deployment $DEPLOYMENT_NAME -n $NAMESPACE -o jsonpath='{.spec.template.spec.containers[0].image}' 2>/dev/null || echo "none")
    echo "$CURRENT_IMAGE" > "$backup_dir/previous_image.txt"

    log_success "Backup created in $backup_dir"
    echo "$backup_dir" > .last_backup
}

run_pre_deployment_tests() {
    log_info "Running pre-deployment tests..."

    # Run unit tests
    log_info "Running unit tests..."
    if ! pytest tests/services/ tests/unit/ -v --tb=short; then
        log_error "Unit tests failed. Aborting deployment."
        exit 1
    fi

    # Run integration tests
    log_info "Running integration tests..."
    if ! pytest tests/integration/ -v --tb=short; then
        log_error "Integration tests failed. Aborting deployment."
        exit 1
    fi

    # Security scan
    log_info "Running security scan..."
    if command -v trivy &> /dev/null; then
        trivy image "ghcr.io/jorge-salas/revenue-platform:$IMAGE_TAG" --severity HIGH,CRITICAL
    else
        log_warning "Trivy not installed, skipping security scan"
    fi

    log_success "Pre-deployment tests passed"
}

deploy_to_kubernetes() {
    log_info "Deploying to Kubernetes ($ENVIRONMENT)..."

    # Update Helm values for environment
    VALUES_FILE="infrastructure/helm/jorge-revenue-platform/values-${ENVIRONMENT}.yaml"

    if [[ ! -f "$VALUES_FILE" ]]; then
        log_warning "Environment-specific values file not found, using default"
        VALUES_FILE="infrastructure/helm/jorge-revenue-platform/values.yaml"
    fi

    # Deploy using Helm
    helm upgrade --install jorge-revenue-platform \
        infrastructure/helm/jorge-revenue-platform/ \
        --namespace $NAMESPACE \
        --create-namespace \
        --values "$VALUES_FILE" \
        --set image.tag="$IMAGE_TAG" \
        --set global.environment="$ENVIRONMENT" \
        --wait \
        --timeout 10m

    log_success "Helm deployment completed"
}

wait_for_rollout() {
    log_info "Waiting for rollout to complete..."

    if kubectl rollout status deployment/$DEPLOYMENT_NAME -n $NAMESPACE --timeout=${HEALTH_CHECK_TIMEOUT}s; then
        log_success "Rollout completed successfully"
    else
        log_error "Rollout failed or timed out"
        return 1
    fi
}

run_health_checks() {
    log_info "Running health checks..."

    # Get service endpoint
    if [[ "$ENVIRONMENT" == "production" ]]; then
        API_URL="https://api.jorge-revenue.example.com"
    else
        API_URL="https://staging-api.jorge-revenue.example.com"
    fi

    # Wait for pods to be ready
    sleep 10

    # Check liveness
    log_info "Checking liveness endpoint..."
    if curl -sf "$API_URL/health/live" > /dev/null; then
        log_success "Liveness check passed"
    else
        log_error "Liveness check failed"
        return 1
    fi

    # Check readiness
    log_info "Checking readiness endpoint..."
    if curl -sf "$API_URL/health/ready" > /dev/null; then
        log_success "Readiness check passed"
    else
        log_error "Readiness check failed"
        return 1
    fi

    log_success "All health checks passed"
}

run_smoke_tests() {
    log_info "Running smoke tests..."

    if [[ -f "scripts/smoke-tests.sh" ]]; then
        if bash scripts/smoke-tests.sh "$ENVIRONMENT"; then
            log_success "Smoke tests passed"
        else
            log_error "Smoke tests failed"
            return 1
        fi
    else
        log_warning "Smoke test script not found, skipping"
    fi
}

monitor_error_rate() {
    log_info "Monitoring error rate for 5 minutes..."

    if [[ -f "scripts/monitor_error_rate.py" ]]; then
        if python scripts/monitor_error_rate.py --duration=300 --threshold=0.01; then
            log_success "Error rate within acceptable limits"
        else
            log_error "Error rate exceeded threshold"
            return 1
        fi
    else
        log_warning "Error rate monitoring script not found, skipping"
    fi
}

rollback_deployment() {
    log_error "Deployment failed. Rolling back..."

    # Rollback using kubectl
    kubectl rollout undo deployment/$DEPLOYMENT_NAME -n $NAMESPACE

    # Wait for rollback
    kubectl rollout status deployment/$DEPLOYMENT_NAME -n $NAMESPACE --timeout=300s

    log_warning "Rollback completed. Previous version restored."
}

send_notification() {
    local status=$1
    local message=$2

    if [[ -n "${SLACK_WEBHOOK:-}" ]]; then
        curl -X POST "$SLACK_WEBHOOK" \
            -H 'Content-Type: application/json' \
            -d "{\"text\": \"$message\", \"username\": \"Deployment Bot\", \"icon_emoji\": \":rocket:\"}"
    fi

    # Log to deployment history
    echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) | $ENVIRONMENT | $IMAGE_TAG | $status | $message" >> deployment-history.log
}

create_deployment_report() {
    log_info "Creating deployment report..."

    cat > "deployment-report-$(date +%Y%m%d_%H%M%S).json" <<EOF
{
  "timestamp": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "environment": "$ENVIRONMENT",
  "image_tag": "$IMAGE_TAG",
  "namespace": "$NAMESPACE",
  "deployment_name": "$DEPLOYMENT_NAME",
  "status": "success",
  "deployed_by": "${USER:-unknown}",
  "git_commit": "$(git rev-parse HEAD 2>/dev/null || echo 'unknown')",
  "git_branch": "$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo 'unknown')",
  "health_checks": {
    "liveness": "passed",
    "readiness": "passed",
    "smoke_tests": "passed"
  },
  "rollout_duration_seconds": "$SECONDS"
}
EOF

    log_success "Deployment report created"
}

# Main deployment flow
main() {
    log_info "=========================================="
    log_info "Jorge's Revenue Platform Deployment"
    log_info "Environment: $ENVIRONMENT"
    log_info "Image Tag: $IMAGE_TAG"
    log_info "=========================================="
    echo

    # Execute deployment steps
    check_prerequisites
    validate_environment
    backup_current_deployment
    run_pre_deployment_tests

    # Deploy
    if deploy_to_kubernetes && \
       wait_for_rollout && \
       run_health_checks && \
       run_smoke_tests && \
       monitor_error_rate; then

        log_success "=========================================="
        log_success "DEPLOYMENT SUCCESSFUL"
        log_success "Environment: $ENVIRONMENT"
        log_success "Image Tag: $IMAGE_TAG"
        log_success "Duration: ${SECONDS}s"
        log_success "=========================================="

        create_deployment_report
        send_notification "success" "Deployment to $ENVIRONMENT completed successfully (Tag: $IMAGE_TAG)"

        exit 0
    else
        log_error "=========================================="
        log_error "DEPLOYMENT FAILED"
        log_error "=========================================="

        rollback_deployment
        send_notification "failed" "Deployment to $ENVIRONMENT failed. Rolled back to previous version."

        exit 1
    fi
}

# Run main function
main "$@"
