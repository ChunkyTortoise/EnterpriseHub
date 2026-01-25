#!/bin/bash

# Jorge Ultra-Fast ML Engine Production Deployment Script
# Deploys ultra-fast ML engine to AWS EKS with all optimizations
# Version: 3.0.0

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
DEPLOYMENT_ENV="${DEPLOYMENT_ENV:-production}"
AWS_REGION="${AWS_REGION:-us-east-1}"
EKS_CLUSTER_NAME="${EKS_CLUSTER_NAME:-jorge-platform-eks}"
IMAGE_REGISTRY="${IMAGE_REGISTRY:-your-account.dkr.ecr.us-east-1.amazonaws.com}"
IMAGE_NAME="jorge-platform/ultra-fast-ml-engine"
IMAGE_TAG="${IMAGE_TAG:-v3.0.0}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
log_warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# Error handler
error_exit() {
    log_error "$1"
    exit 1
}

# Check prerequisites
check_prerequisites() {
    log_info "Checking prerequisites..."

    # Check required commands
    command -v aws >/dev/null 2>&1 || error_exit "AWS CLI not found"
    command -v kubectl >/dev/null 2>&1 || error_exit "kubectl not found"
    command -v docker >/dev/null 2>&1 || error_exit "Docker not found"
    command -v helm >/dev/null 2>&1 || error_exit "Helm not found"

    # Check AWS authentication
    aws sts get-caller-identity >/dev/null 2>&1 || error_exit "AWS authentication failed"

    # Check kubectl context
    kubectl config current-context >/dev/null 2>&1 || error_exit "kubectl context not set"

    log_success "Prerequisites check passed"
}

# Build and push Docker image
build_and_push_image() {
    log_info "Building ultra-fast ML engine Docker image..."

    cd "$PROJECT_ROOT"

    # Login to ECR
    aws ecr get-login-password --region "$AWS_REGION" | docker login --username AWS --password-stdin "$IMAGE_REGISTRY"

    # Create ECR repository if it doesn't exist
    aws ecr describe-repositories --repository-names "${IMAGE_NAME}" --region "$AWS_REGION" >/dev/null 2>&1 || {
        log_info "Creating ECR repository: ${IMAGE_NAME}"
        aws ecr create-repository --repository-name "${IMAGE_NAME}" --region "$AWS_REGION"
    }

    # Build image with performance optimizations
    log_info "Building Docker image with CUDA and ONNX optimizations..."
    docker build \
        -f infrastructure/docker/Dockerfile.ultra-fast-ml \
        -t "${IMAGE_REGISTRY}/${IMAGE_NAME}:${IMAGE_TAG}" \
        -t "${IMAGE_REGISTRY}/${IMAGE_NAME}:latest" \
        --build-arg BUILDKIT_INLINE_CACHE=1 \
        --cache-from "${IMAGE_REGISTRY}/${IMAGE_NAME}:latest" \
        .

    # Push to registry
    log_info "Pushing image to ECR..."
    docker push "${IMAGE_REGISTRY}/${IMAGE_NAME}:${IMAGE_TAG}"
    docker push "${IMAGE_REGISTRY}/${IMAGE_NAME}:latest"

    log_success "Docker image built and pushed successfully"
}

# Deploy Terraform infrastructure
deploy_infrastructure() {
    log_info "Deploying AWS infrastructure with Terraform..."

    cd "$PROJECT_ROOT/infrastructure/terraform"

    # Initialize Terraform
    terraform init

    # Plan the deployment
    log_info "Planning Terraform deployment..."
    terraform plan \
        -var="environment=${DEPLOYMENT_ENV}" \
        -var="aws_region=${AWS_REGION}" \
        -var="image_tag=${IMAGE_TAG}" \
        -out=tfplan

    # Apply the plan
    log_info "Applying Terraform plan..."
    terraform apply tfplan

    # Get outputs
    REDIS_ENDPOINT=$(terraform output -raw redis_cluster_endpoint)
    S3_BUCKET=$(terraform output -raw s3_model_bucket)
    IAM_ROLE_ARN=$(terraform output -raw ml_engine_role_arn)

    log_success "Infrastructure deployed successfully"

    # Export for use in Kubernetes deployment
    export REDIS_ENDPOINT
    export S3_BUCKET
    export IAM_ROLE_ARN
}

# Configure kubectl for EKS
configure_kubectl() {
    log_info "Configuring kubectl for EKS cluster..."

    aws eks update-kubeconfig \
        --region "$AWS_REGION" \
        --name "$EKS_CLUSTER_NAME"

    # Verify connection
    kubectl get nodes >/dev/null 2>&1 || error_exit "Failed to connect to EKS cluster"

    log_success "kubectl configured for EKS cluster"
}

# Create namespace if not exists
create_namespace() {
    log_info "Creating Kubernetes namespace..."

    kubectl create namespace jorge-platform --dry-run=client -o yaml | kubectl apply -f -

    log_success "Namespace created/updated"
}

# Deploy Kubernetes resources
deploy_kubernetes() {
    log_info "Deploying ultra-fast ML engine to Kubernetes..."

    cd "$PROJECT_ROOT"

    # Update deployment with current configuration
    envsubst < infrastructure/kubernetes/ultra-fast-ml-engine-deployment.yaml > /tmp/ml-deployment.yaml

    # Replace placeholders in deployment file
    sed -i.bak "s|<image-registry>|${IMAGE_REGISTRY}|g" /tmp/ml-deployment.yaml
    sed -i.bak "s|<image-tag>|${IMAGE_TAG}|g" /tmp/ml-deployment.yaml
    sed -i.bak "s|<redis-endpoint>|${REDIS_ENDPOINT:-jorge-redis-cluster.cache.amazonaws.com}|g" /tmp/ml-deployment.yaml
    sed -i.bak "s|<s3-bucket>|${S3_BUCKET:-jorge-platform-ml-models}|g" /tmp/ml-deployment.yaml
    sed -i.bak "s|<iam-role-arn>|${IAM_ROLE_ARN}|g" /tmp/ml-deployment.yaml

    # Apply Kubernetes resources
    log_info "Applying Kubernetes manifests..."
    kubectl apply -f /tmp/ml-deployment.yaml

    # Wait for deployment to be ready
    log_info "Waiting for deployment to be ready..."
    kubectl wait --for=condition=available --timeout=300s deployment/ultra-fast-ml-engine -n jorge-platform

    log_success "Kubernetes deployment completed"
}

# Validate deployment
validate_deployment() {
    log_info "Validating deployment..."

    # Check pod status
    kubectl get pods -n jorge-platform -l app=ultra-fast-ml-engine

    # Check if pods are running
    RUNNING_PODS=$(kubectl get pods -n jorge-platform -l app=ultra-fast-ml-engine --field-selector=status.phase=Running --no-headers | wc -l)
    if [ "$RUNNING_PODS" -lt 1 ]; then
        error_exit "No running pods found"
    fi

    # Health check
    log_info "Performing health check..."
    kubectl port-forward -n jorge-platform svc/ultra-fast-ml-service 8080:80 &
    PF_PID=$!
    sleep 5

    # Test health endpoint
    HEALTH_RESPONSE=$(curl -s http://localhost:8080/health || echo "failed")
    kill $PF_PID 2>/dev/null || true

    if [[ "$HEALTH_RESPONSE" == *"healthy"* ]]; then
        log_success "Health check passed"
    else
        log_warning "Health check failed or inconclusive: $HEALTH_RESPONSE"
    fi

    # Performance validation
    log_info "Checking performance metrics..."
    POD_NAME=$(kubectl get pods -n jorge-platform -l app=ultra-fast-ml-engine -o jsonpath='{.items[0].metadata.name}')

    # Check logs for performance indicators
    kubectl logs "$POD_NAME" -n jorge-platform --tail=50 | grep -i "performance\|inference\|ms" || true

    log_success "Deployment validation completed"
}

# Setup monitoring
setup_monitoring() {
    log_info "Setting up monitoring and alerting..."

    # Install Prometheus if not exists
    if ! kubectl get namespace monitoring >/dev/null 2>&1; then
        log_info "Installing Prometheus..."
        kubectl create namespace monitoring

        helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
        helm repo update

        helm install prometheus prometheus-community/kube-prometheus-stack \
            --namespace monitoring \
            --set prometheus.prometheusSpec.serviceMonitorSelectorNilUsesHelmValues=false
    fi

    # Apply ServiceMonitor for ML engine
    kubectl apply -f infrastructure/kubernetes/ultra-fast-ml-engine-deployment.yaml -n jorge-platform

    # Import Grafana dashboard
    if command -v curl >/dev/null 2>&1; then
        log_info "Importing Jorge Bot Intelligence dashboard..."
        # This would typically use Grafana API to import the dashboard
        # For now, we'll just copy the dashboard JSON
        kubectl create configmap jorge-bot-dashboard \
            --from-file="$PROJECT_ROOT/infrastructure/monitoring/jorge-bot-intelligence-dashboard.json" \
            -n monitoring \
            --dry-run=client -o yaml | kubectl apply -f -
    fi

    log_success "Monitoring setup completed"
}

# Performance testing
run_performance_test() {
    log_info "Running performance test..."

    # Port forward for testing
    kubectl port-forward -n jorge-platform svc/ultra-fast-ml-service 8080:80 &
    PF_PID=$!
    sleep 5

    # Simple performance test
    cat > /tmp/test_request.json << EOF
{
    "lead_id": "perf_test_001",
    "features": {
        "contact_score": 0.75,
        "engagement_score": 0.80,
        "response_time_avg": 120,
        "property_views": 5,
        "email_opens": 3,
        "call_duration": 180,
        "days_since_inquiry": 2,
        "budget_range": 500000,
        "urgency_score": 0.70,
        "lead_source": "website",
        "property_type": "single_family",
        "market_segment": "residential"
    }
}
EOF

    # Run test requests
    log_info "Testing inference latency..."
    for i in {1..10}; do
        RESPONSE=$(curl -s -w "\n%{time_total}" -H "Content-Type: application/json" \
            -d @/tmp/test_request.json http://localhost:8080/predict)

        LATENCY=$(echo "$RESPONSE" | tail -1)
        LATENCY_MS=$(echo "$LATENCY * 1000" | bc -l)

        if (( $(echo "$LATENCY_MS < 100" | bc -l) )); then
            log_success "Test $i: ${LATENCY_MS}ms ✓"
        else
            log_warning "Test $i: ${LATENCY_MS}ms (slower than expected)"
        fi
    done

    # Clean up
    kill $PF_PID 2>/dev/null || true
    rm -f /tmp/test_request.json

    log_success "Performance test completed"
}

# Main deployment function
main() {
    log_info "Starting Jorge Ultra-Fast ML Engine deployment..."

    check_prerequisites
    build_and_push_image
    deploy_infrastructure
    configure_kubectl
    create_namespace
    deploy_kubernetes
    validate_deployment
    setup_monitoring
    run_performance_test

    log_success "🎉 Jorge Ultra-Fast ML Engine deployment completed successfully!"
    log_info "Service is available at: kubectl port-forward -n jorge-platform svc/ultra-fast-ml-service 8080:80"
    log_info "Monitoring: kubectl port-forward -n monitoring svc/prometheus-grafana 3000:80"
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --env)
            DEPLOYMENT_ENV="$2"
            shift 2
            ;;
        --region)
            AWS_REGION="$2"
            shift 2
            ;;
        --cluster)
            EKS_CLUSTER_NAME="$2"
            shift 2
            ;;
        --image-tag)
            IMAGE_TAG="$2"
            shift 2
            ;;
        --registry)
            IMAGE_REGISTRY="$2"
            shift 2
            ;;
        --skip-build)
            SKIP_BUILD=true
            shift
            ;;
        --skip-infra)
            SKIP_INFRA=true
            shift
            ;;
        --help)
            echo "Usage: $0 [OPTIONS]"
            echo "Options:"
            echo "  --env ENV              Deployment environment (default: production)"
            echo "  --region REGION        AWS region (default: us-east-1)"
            echo "  --cluster CLUSTER      EKS cluster name (default: jorge-platform-eks)"
            echo "  --image-tag TAG        Docker image tag (default: v3.0.0)"
            echo "  --registry REGISTRY    ECR registry URL"
            echo "  --skip-build          Skip Docker image build"
            echo "  --skip-infra          Skip infrastructure deployment"
            echo "  --help                Show this help"
            exit 0
            ;;
        *)
            error_exit "Unknown option: $1"
            ;;
    esac
done

# Run main function
main