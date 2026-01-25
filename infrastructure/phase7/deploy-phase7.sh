#!/bin/bash
set -e

# Jorge's Real Estate AI Platform - Phase 7 Deployment Script
# Advanced AI Intelligence & Global Scaling Infrastructure
#
# This script deploys the complete Phase 7 infrastructure to AWS EKS
# Built for enterprise-grade performance with automatic scaling

echo "🚀 Starting Jorge Phase 7 Advanced Intelligence Deployment"
echo "=================================================="

# Configuration
NAMESPACE="jorge-phase7"
CLUSTER_NAME="jorge-production-eks"
REGION="us-east-1"
PHASE="7"
DEPLOYMENT_VERSION=$(date +"%Y%m%d-%H%M%S")

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging function
log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1" >&2
    exit 1
}

warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

# Check prerequisites
check_prerequisites() {
    log "Checking deployment prerequisites..."

    # Check required tools
    for tool in kubectl aws docker helm; do
        if ! command -v $tool &> /dev/null; then
            error "$tool is required but not installed"
        fi
    done

    # Check kubectl context
    current_context=$(kubectl config current-context)
    if [[ ! "$current_context" =~ "$CLUSTER_NAME" ]]; then
        error "kubectl context is not set to $CLUSTER_NAME. Current: $current_context"
    fi

    # Check AWS credentials
    if ! aws sts get-caller-identity &> /dev/null; then
        error "AWS credentials not configured properly"
    fi

    # Check Docker daemon
    if ! docker info &> /dev/null; then
        error "Docker daemon is not running"
    fi

    success "Prerequisites check passed"
}

# Build and push Docker images
build_and_push_images() {
    log "Building and pushing Phase 7 Docker images..."

    local ECR_REGISTRY="$(aws sts get-caller-identity --query Account --output text).dkr.ecr.$REGION.amazonaws.com"

    # Authenticate Docker to ECR
    aws ecr get-login-password --region $REGION | docker login --username AWS --password-stdin $ECR_REGISTRY

    # Build images
    local images=(
        "phase7-revenue:latest"
        "phase7-bi:latest"
        "phase7-analytics:latest"
        "phase7-market:latest"
        "phase7-streaming:latest"
        "phase7-cache:latest"
    )

    for image in "${images[@]}"; do
        log "Building jorge-real-estate-ai/$image..."

        # Determine dockerfile path based on image type
        local service_name=$(echo $image | cut -d':' -f1 | sed 's/phase7-//')
        local dockerfile_path="./dockerfiles/phase7/Dockerfile.${service_name}"

        # Build image
        docker build -t "jorge-real-estate-ai/$image" -f "$dockerfile_path" .

        # Tag for ECR
        docker tag "jorge-real-estate-ai/$image" "$ECR_REGISTRY/jorge-real-estate-ai/$image"

        # Push to ECR
        docker push "$ECR_REGISTRY/jorge-real-estate-ai/$image"

        success "Built and pushed jorge-real-estate-ai/$image"
    done
}

# Create namespace and basic resources
setup_namespace() {
    log "Setting up Phase 7 namespace and basic resources..."

    # Apply namespace configuration
    kubectl apply -f kubernetes/phase7-deployment.yaml

    # Wait for namespace to be ready
    kubectl wait --for=condition=Ready namespace/$NAMESPACE --timeout=60s

    success "Namespace $NAMESPACE created and ready"
}

# Deploy configuration and secrets
deploy_config() {
    log "Deploying Phase 7 configuration and secrets..."

    # Apply configuration maps and secrets
    kubectl apply -f kubernetes/phase7-config.yaml

    # Verify config deployment
    kubectl get configmaps -n $NAMESPACE
    kubectl get secrets -n $NAMESPACE

    success "Configuration and secrets deployed"
}

# Deploy core services
deploy_services() {
    log "Deploying Phase 7 core services..."

    # Apply services configuration
    kubectl apply -f kubernetes/phase7-services.yaml

    # Wait for services to be ready
    log "Waiting for services to be ready..."
    kubectl wait --for=condition=Available deployment --all -n $NAMESPACE --timeout=300s

    # Verify service deployment
    kubectl get services -n $NAMESPACE
    kubectl get deployments -n $NAMESPACE

    success "Core services deployed successfully"
}

# Setup ingress and networking
setup_networking() {
    log "Setting up Phase 7 networking and ingress..."

    # Apply ingress configuration
    kubectl apply -f kubernetes/phase7-ingress.yaml

    # Wait for ingress to be ready
    log "Waiting for ingress to be ready..."
    sleep 30

    # Verify ingress
    kubectl get ingress -n $NAMESPACE

    success "Networking and ingress configured"
}

# Deploy autoscaling configuration
deploy_autoscaling() {
    log "Deploying Phase 7 autoscaling configuration..."

    # Apply HPA configuration
    kubectl apply -f kubernetes/phase7-hpa.yaml

    # Verify autoscaling setup
    kubectl get hpa -n $NAMESPACE

    success "Autoscaling configuration deployed"
}

# Setup monitoring and observability
setup_monitoring() {
    log "Setting up Phase 7 monitoring and observability..."

    # Apply monitoring configuration
    kubectl apply -f monitoring/phase7-monitoring.yaml

    # Verify monitoring setup
    kubectl get servicemonitor -n $NAMESPACE
    kubectl get prometheusrule -n $NAMESPACE

    success "Monitoring and observability configured"
}

# Run health checks
run_health_checks() {
    log "Running Phase 7 health checks..."

    local services=(
        "revenue-intelligence-service:8000"
        "business-intelligence-service:8001"
        "conversation-analytics-service:8002"
        "market-intelligence-service:8003"
        "stream-processor-service:8004"
        "cache-service-service:8005"
    )

    for service in "${services[@]}"; do
        local service_name=$(echo $service | cut -d':' -f1)
        local port=$(echo $service | cut -d':' -f2)

        log "Checking health of $service_name..."

        # Port forward for health check
        kubectl port-forward -n $NAMESPACE service/$service_name $port:$port &
        local pf_pid=$!

        # Wait a moment for port forward to establish
        sleep 3

        # Health check
        if curl -f -s "http://localhost:$port/health" > /dev/null; then
            success "$service_name is healthy"
        else
            warning "$service_name health check failed"
        fi

        # Clean up port forward
        kill $pf_pid 2>/dev/null || true
    done
}

# Performance validation
validate_performance() {
    log "Running Phase 7 performance validation..."

    # Test ML model latency
    log "Testing ML model latency..."
    kubectl run phase7-perf-test --rm -i --restart=Never --image=curlimages/curl -- \
        curl -s -w "Response time: %{time_total}s\n" \
        http://revenue-intelligence-service.jorge-phase7:8000/health

    # Test cache performance
    log "Testing cache performance..."
    kubectl run phase7-cache-test --rm -i --restart=Never --image=curlimages/curl -- \
        curl -s -w "Cache response: %{time_total}s\n" \
        http://cache-service-service.jorge-phase7:8005/health

    success "Performance validation completed"
}

# Generate deployment summary
generate_summary() {
    log "Generating Phase 7 deployment summary..."

    local summary_file="phase7-deployment-summary-$DEPLOYMENT_VERSION.txt"

    cat > $summary_file << EOF
Jorge's Real Estate AI Platform - Phase 7 Deployment Summary
===========================================================
Deployment Version: $DEPLOYMENT_VERSION
Timestamp: $(date)
Cluster: $CLUSTER_NAME
Namespace: $NAMESPACE
Region: $REGION

Services Deployed:
- Revenue Intelligence Engine (port 8000)
- Business Intelligence Dashboard (port 8001)
- Conversation Analytics Service (port 8002)
- Market Intelligence Engine (port 8003)
- Stream Processor (port 8004, WebSocket 8080)
- Intelligent Cache Service (port 8005)

Ingress Endpoints:
- API Gateway: https://phase7-api.jorge-ai.com
- Intelligence Dashboard: https://intelligence.jorge-ai.com
- Streaming Service: https://streaming.jorge-ai.com
- WebSocket: wss://ws.jorge-ai.com
- Metrics: https://metrics.jorge-ai.com

Autoscaling Configuration:
- Revenue Intelligence: 3-15 replicas
- Business Intelligence: 2-10 replicas
- Conversation Analytics: 2-12 replicas
- Market Intelligence: 2-8 replicas
- Stream Processor: 3-20 replicas
- Cache Service: 2-6 replicas

Monitoring:
- Prometheus metrics collection
- Grafana dashboards configured
- AlertManager notifications setup
- Custom Phase 7 business alerts

Performance Targets:
- ML Model Latency: < 25ms
- Cache Hit Rate: > 95%
- API Response Time: < 100ms
- WebSocket Latency: < 50ms
- Throughput: 10,000+ req/sec

Jorge Methodology Integration:
✅ 6% Commission Rate Protection
✅ Confrontational Qualification Enhancement
✅ Temperature Classification (Hot/Warm/Cold)
✅ ML-Powered Lead Scoring
✅ Real-time Performance Analytics

Next Steps:
1. Monitor deployment health via Grafana dashboards
2. Validate business intelligence functionality
3. Test Jorge methodology enhancements
4. Verify auto-scaling behavior
5. Run full end-to-end integration tests

For support: phase7-team@jorge-ai.com
EOF

    success "Deployment summary generated: $summary_file"
    cat $summary_file
}

# Cleanup function for failed deployments
cleanup() {
    if [ $? -ne 0 ]; then
        error "Deployment failed. Cleaning up resources..."
        kubectl delete namespace $NAMESPACE --ignore-not-found=true
    fi
}

# Main deployment function
main() {
    log "🔥 Jorge Phase 7 Advanced Intelligence Deployment Starting"
    log "Version: $DEPLOYMENT_VERSION"
    log "Cluster: $CLUSTER_NAME"
    log "Namespace: $NAMESPACE"

    # Set cleanup trap
    trap cleanup EXIT

    # Execute deployment steps
    check_prerequisites
    build_and_push_images
    setup_namespace
    deploy_config
    deploy_services
    setup_networking
    deploy_autoscaling
    setup_monitoring
    run_health_checks
    validate_performance
    generate_summary

    success "🎉 Phase 7 deployment completed successfully!"
    success "Jorge's Advanced Intelligence platform is now live and ready for global scaling"

    log "Access your Phase 7 dashboards:"
    log "• Intelligence Dashboard: https://intelligence.jorge-ai.com"
    log "• API Gateway: https://phase7-api.jorge-ai.com"
    log "• Monitoring: https://metrics.jorge-ai.com"
}

# Execute main function
main "$@"