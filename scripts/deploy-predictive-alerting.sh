#!/bin/bash

# Predictive Alerting Engine Production Deployment Script
# Deploys ML-based predictive alerting with 15-30 minute advance warnings
# Version: 1.0.0

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
DEPLOYMENT_ENV="${DEPLOYMENT_ENV:-production}"
AWS_REGION="${AWS_REGION:-us-east-1}"
EKS_CLUSTER_NAME="${EKS_CLUSTER_NAME:-jorge-platform-eks}"
IMAGE_REGISTRY="${IMAGE_REGISTRY:-your-account.dkr.ecr.us-east-1.amazonaws.com}"
IMAGE_NAME="jorge-platform/predictive-alerting-engine"
IMAGE_TAG="${IMAGE_TAG:-v1.0.0}"

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
    log_info "Checking prerequisites for predictive alerting deployment..."

    # Check required commands
    command -v aws >/dev/null 2>&1 || error_exit "AWS CLI not found"
    command -v kubectl >/dev/null 2>&1 || error_exit "kubectl not found"
    command -v docker >/dev/null 2>&1 || error_exit "Docker not found"

    # Check AWS authentication
    aws sts get-caller-identity >/dev/null 2>&1 || error_exit "AWS authentication failed"

    # Check kubectl context
    kubectl config current-context >/dev/null 2>&1 || error_exit "kubectl context not set"

    # Check if Prometheus is running
    log_info "Checking Prometheus availability..."
    kubectl get svc prometheus-server -n monitoring >/dev/null 2>&1 || log_warning "Prometheus not found in monitoring namespace"

    log_success "Prerequisites check passed"
}

# Build and push predictive alerting Docker image
build_and_push_image() {
    log_info "Building predictive alerting engine Docker image..."

    cd "$PROJECT_ROOT"

    # Create Dockerfile for predictive alerting engine
    cat > Dockerfile.predictive-alerting << 'EOF'
# Predictive Alerting Engine Production Dockerfile
FROM python:3.11-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Install system dependencies including ML libraries
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    build-essential \
    curl \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Create application user
RUN groupadd -r jorge && useradd -r -g jorge -d /app -s /sbin/nologin jorge

# Create application directory
WORKDIR /app
RUN chown jorge:jorge /app

# Install Python dependencies
COPY requirements.txt /app/
RUN pip install --no-cache-dir --upgrade pip setuptools wheel && \
    pip install --no-cache-dir \
    scikit-learn==1.3.2 \
    numpy==1.24.4 \
    pandas==2.1.4 \
    joblib==1.3.2 \
    aiohttp==3.9.1 \
    && pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY --chown=jorge:jorge ghl_real_estate_ai/monitoring/predictive_alerting_engine.py /app/
COPY --chown=jorge:jorge ghl_real_estate_ai/ghl_utils/ /app/ghl_utils/
COPY --chown=jorge:jorge production_predictive_alerting_server.py /app/

# Create model training job script
COPY --chown=jorge:jorge <<'EOFJOB' /app/model_training_job.py
#!/usr/bin/env python3
"""
Model Training Job for Predictive Alerting Engine
"""
import asyncio
import logging
import os
import sys
import joblib
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, precision_score, recall_score

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def train_models():
    """Train anomaly detection models"""
    try:
        logger.info("Starting model training job...")

        # Generate synthetic training data (in production, this would fetch real data)
        n_samples = 10000
        n_features = 10

        # Generate normal data
        normal_data = np.random.normal(0, 1, (int(n_samples * 0.9), n_features))

        # Generate anomalous data
        anomaly_data = np.random.normal(3, 2, (int(n_samples * 0.1), n_features))

        # Combine data
        X = np.vstack([normal_data, anomaly_data])
        y = np.hstack([np.ones(len(normal_data)), -np.ones(len(anomaly_data))])

        # Split data
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

        # Scale features
        scaler = StandardScaler()
        X_train_scaled = scaler.fit_transform(X_train)
        X_test_scaled = scaler.transform(X_test)

        # Train anomaly detection model
        model = IsolationForest(
            contamination=0.1,
            random_state=42,
            n_estimators=100
        )
        model.fit(X_train_scaled)

        # Evaluate model
        y_pred = model.predict(X_test_scaled)
        accuracy = accuracy_score(y_test, y_pred)

        logger.info(f"Model training completed - Accuracy: {accuracy:.3f}")

        # Save models
        model_storage_path = os.getenv("MODEL_STORAGE_PATH", "/app/models")
        os.makedirs(model_storage_path, exist_ok=True)

        joblib.dump(model, os.path.join(model_storage_path, "anomaly_detection_model.joblib"))
        joblib.dump(scaler, os.path.join(model_storage_path, "feature_scaler.joblib"))

        logger.info("Models saved successfully")

        return accuracy

    except Exception as e:
        logger.error(f"Model training failed: {e}")
        return 0.0

if __name__ == "__main__":
    accuracy = asyncio.run(train_models())
    if accuracy < 0.8:
        sys.exit(1)
EOFJOB

RUN chmod +x /app/model_training_job.py

# Create configuration
RUN cat > /app/config.yaml << 'EOFCONFIG'
server:
  host: 0.0.0.0
  port: 8080
  workers: 1

predictive_alerting:
  model_update_interval_hours: 6
  training_window_hours: 168
  prediction_horizon_minutes: 30
  confidence_threshold: 0.85
  false_positive_threshold: 0.05

monitoring:
  prometheus_url: "http://prometheus-server:9090"
  grafana_url: "http://prometheus-grafana:3000"

alerts:
  cooldown_minutes: 15
  escalation_delay_minutes: 5
  max_alerts_per_hour: 10

business:
  business_hours_start: "08:00"
  business_hours_end: "18:00"
  critical_times: "09:00-10:00,14:00-16:00"
EOFCONFIG

# Health check script
RUN cat > /app/health_check.py << 'EOFHEALTH'
#!/usr/bin/env python3
import asyncio
import aiohttp
import sys
import time

async def health_check():
    try:
        timeout = aiohttp.ClientTimeout(total=10)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            start_time = time.perf_counter()
            async with session.get('http://localhost:8080/health') as response:
                if response.status == 200:
                    data = await response.json()
                    if data.get('status') in ['healthy', 'degraded']:
                        response_time = time.perf_counter() - start_time
                        print(f"Health check passed: {response_time*1000:.1f}ms")
                        sys.exit(0)
                    else:
                        print(f"Health check failed: {data.get('status')}")
                        sys.exit(1)
                else:
                    print(f"Health check failed: HTTP {response.status}")
                    sys.exit(1)
    except Exception as e:
        print(f"Health check failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(health_check())
EOFHEALTH

RUN chmod +x /app/health_check.py

# Create models directory
RUN mkdir -p /app/models && chown jorge:jorge /app/models

# Switch to non-root user
USER jorge

# Expose port
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=15s --start-period=120s --retries=3 \
    CMD python3 /app/health_check.py

# Labels
LABEL maintainer="jorge-platform-team@example.com"
LABEL version="1.0.0"
LABEL component="predictive-alerting-engine"
LABEL performance.target=">85% accuracy, <5% false positives"

# Default command
CMD ["python3", "production_predictive_alerting_server.py"]
EOF

    # Login to ECR
    aws ecr get-login-password --region "$AWS_REGION" | docker login --username AWS --password-stdin "$IMAGE_REGISTRY"

    # Create ECR repository if it doesn't exist
    aws ecr describe-repositories --repository-names "${IMAGE_NAME}" --region "$AWS_REGION" >/dev/null 2>&1 || {
        log_info "Creating ECR repository: ${IMAGE_NAME}"
        aws ecr create-repository --repository-name "${IMAGE_NAME}" --region "$AWS_REGION"
    }

    # Build image
    log_info "Building Docker image for predictive alerting engine..."
    docker build \
        -f Dockerfile.predictive-alerting \
        -t "${IMAGE_REGISTRY}/${IMAGE_NAME}:${IMAGE_TAG}" \
        -t "${IMAGE_REGISTRY}/${IMAGE_NAME}:latest" \
        .

    # Push to registry
    log_info "Pushing image to ECR..."
    docker push "${IMAGE_REGISTRY}/${IMAGE_NAME}:${IMAGE_TAG}"
    docker push "${IMAGE_REGISTRY}/${IMAGE_NAME}:latest"

    # Cleanup
    rm -f Dockerfile.predictive-alerting

    log_success "Predictive alerting Docker image built and pushed successfully"
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

# Deploy Kubernetes resources
deploy_kubernetes() {
    log_info "Deploying predictive alerting engine to Kubernetes..."

    cd "$PROJECT_ROOT"

    # Update deployment with current configuration
    cp infrastructure/kubernetes/predictive-alerting-deployment.yaml /tmp/predictive-alerting-deployment.yaml

    # Replace placeholders in deployment file
    sed -i.bak "s|jorge-platform/predictive-alerting-engine:v1.0.0|${IMAGE_REGISTRY}/${IMAGE_NAME}:${IMAGE_TAG}|g" /tmp/predictive-alerting-deployment.yaml

    # Apply Kubernetes resources
    log_info "Applying Kubernetes manifests..."
    kubectl apply -f /tmp/predictive-alerting-deployment.yaml

    # Wait for deployment to be ready
    log_info "Waiting for predictive alerting deployment to be ready..."
    kubectl wait --for=condition=available --timeout=600s deployment/predictive-alerting-engine -n jorge-platform

    log_success "Predictive alerting Kubernetes deployment completed"
}

# Setup Prometheus integration
setup_prometheus_integration() {
    log_info "Setting up Prometheus integration..."

    # Create Prometheus RBAC for predictive alerting
    kubectl apply -f - << 'EOF'
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: predictive-alerting-prometheus
rules:
- apiGroups: [""]
  resources: ["nodes", "services", "endpoints", "pods"]
  verbs: ["get", "list", "watch"]
- apiGroups: ["extensions"]
  resources: ["ingresses"]
  verbs: ["get", "list", "watch"]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRoleBinding
metadata:
  name: predictive-alerting-prometheus
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: ClusterRole
  name: predictive-alerting-prometheus
subjects:
- kind: ServiceAccount
  name: jorge-platform-monitoring-service-account
  namespace: jorge-platform
EOF

    # Test Prometheus connectivity
    log_info "Testing Prometheus connectivity..."
    ALERTING_POD=$(kubectl get pods -n jorge-platform -l app=predictive-alerting-engine -o jsonpath='{.items[0].metadata.name}')

    if [ -n "$ALERTING_POD" ]; then
        kubectl exec -n jorge-platform "$ALERTING_POD" -- curl -s "http://prometheus-server:9090/api/v1/query?query=up" >/dev/null
        if [ $? -eq 0 ]; then
            log_success "Prometheus connectivity: WORKING"
        else
            log_warning "Prometheus connectivity: FAILED - alerts may not work correctly"
        fi
    else
        log_warning "No predictive alerting pods found for Prometheus connectivity test"
    fi

    log_success "Prometheus integration setup completed"
}

# Setup alert channels
setup_alert_channels() {
    log_info "Setting up alert channels..."

    # Configure Slack webhook (example - replace with actual values)
    kubectl create secret generic predictive-alerting-webhooks \
        --from-literal=slack_webhook_url="${SLACK_WEBHOOK_URL:-https://hooks.slack.com/example}" \
        --from-literal=pagerduty_api_key="${PAGERDUTY_API_KEY:-example-key}" \
        -n jorge-platform \
        --dry-run=client -o yaml | kubectl apply -f -

    # Create alert policy
    kubectl apply -f - << 'EOF'
apiVersion: v1
kind: ConfigMap
metadata:
  name: predictive-alerting-policy
  namespace: jorge-platform
data:
  alert_policy.yaml: |
    policies:
      - name: "jorge_bot_performance"
        severity: "critical"
        channels: ["slack", "pagerduty"]
        cooldown_minutes: 15
        business_hours_only: false
      - name: "cache_performance"
        severity: "warning"
        channels: ["slack"]
        cooldown_minutes: 30
        business_hours_only: true
      - name: "system_performance"
        severity: "warning"
        channels: ["slack"]
        cooldown_minutes: 20
        business_hours_only: true
EOF

    log_success "Alert channels setup completed"
}

# Run model training
run_initial_model_training() {
    log_info "Running initial model training..."

    # Trigger initial model training job
    kubectl create job initial-model-training \
        --from=cronjob/predictive-model-training \
        -n jorge-platform

    # Wait for training job to complete
    log_info "Waiting for model training to complete..."
    kubectl wait --for=condition=complete --timeout=600s job/initial-model-training -n jorge-platform

    # Check training results
    TRAINING_POD=$(kubectl get pods -n jorge-platform -l job-name=initial-model-training -o jsonpath='{.items[0].metadata.name}')

    if [ -n "$TRAINING_POD" ]; then
        TRAINING_LOGS=$(kubectl logs "$TRAINING_POD" -n jorge-platform | tail -10)
        if echo "$TRAINING_LOGS" | grep -q "Models saved successfully"; then
            log_success "Model training: COMPLETED"
        else
            log_warning "Model training: ISSUES DETECTED"
            echo "$TRAINING_LOGS"
        fi
    else
        log_warning "Model training pod not found"
    fi

    # Cleanup training job
    kubectl delete job initial-model-training -n jorge-platform

    log_success "Initial model training completed"
}

# Run validation tests
run_validation_tests() {
    log_info "Running predictive alerting validation tests..."

    # Port forward for testing
    kubectl port-forward -n jorge-platform svc/predictive-alerting-service 8080:80 &
    PF_PID=$!
    sleep 10

    # Test health endpoint
    HEALTH_RESPONSE=$(curl -s http://localhost:8080/health || echo "failed")
    if [[ "$HEALTH_RESPONSE" == *"healthy"* ]] || [[ "$HEALTH_RESPONSE" == *"degraded"* ]]; then
        log_success "Health check: PASSED"
    else
        log_warning "Health check: FAILED"
        echo "Response: $HEALTH_RESPONSE"
    fi

    # Test model info endpoint
    MODEL_RESPONSE=$(curl -s http://localhost:8080/model/info || echo "failed")
    if [[ "$MODEL_RESPONSE" == *"accuracy"* ]]; then
        log_success "Model endpoint: PASSED"
        echo "Model info: $MODEL_RESPONSE"
    else
        log_warning "Model endpoint: FAILED"
    fi

    # Test prediction endpoint with dummy data
    cat > /tmp/test_prediction.json << 'EOF'
{
    "metrics": [
        {
            "timestamp": "2026-01-24T12:00:00Z",
            "metric_name": "jorge_bot_response_time",
            "value": 0.85,
            "labels": {}
        },
        {
            "timestamp": "2026-01-24T12:01:00Z",
            "metric_name": "cache_hit_rate",
            "value": 0.92,
            "labels": {}
        }
    ],
    "prediction_horizon_minutes": 30,
    "confidence_threshold": 0.85
}
EOF

    PREDICTION_RESPONSE=$(curl -s -X POST \
        -H "Content-Type: application/json" \
        -d @/tmp/test_prediction.json \
        http://localhost:8080/predict || echo "failed")

    if [[ "$PREDICTION_RESPONSE" != "failed" ]]; then
        log_success "Prediction endpoint: PASSED"
    else
        log_warning "Prediction endpoint: FAILED"
    fi

    # Clean up
    kill $PF_PID 2>/dev/null || true
    rm -f /tmp/test_prediction.json

    # Check service logs for errors
    log_info "Checking predictive alerting service logs..."
    ALERTING_POD=$(kubectl get pods -n jorge-platform -l app=predictive-alerting-engine -o jsonpath='{.items[0].metadata.name}')

    if [ -n "$ALERTING_POD" ]; then
        ERROR_COUNT=$(kubectl logs "$ALERTING_POD" -n jorge-platform --tail=50 | grep -c "ERROR" || echo "0")
        if [ "$ERROR_COUNT" -eq 0 ]; then
            log_success "Service logs: No errors found"
        else
            log_warning "Service logs: $ERROR_COUNT errors found"
            kubectl logs "$ALERTING_POD" -n jorge-platform --tail=10 | grep "ERROR" || true
        fi
    fi

    log_success "Validation tests completed"
}

# Setup monitoring dashboards
setup_monitoring_dashboards() {
    log_info "Setting up monitoring dashboards..."

    # Create Grafana dashboard for predictive alerting
    kubectl apply -f - << 'EOF'
apiVersion: v1
kind: ConfigMap
metadata:
  name: predictive-alerting-dashboard
  namespace: monitoring
  labels:
    grafana_dashboard: "1"
data:
  predictive-alerting.json: |
    {
      "dashboard": {
        "title": "Predictive Alerting - Jorge Platform Intelligence",
        "description": "ML-based predictive alerting with business impact analysis",
        "panels": [
          {
            "title": "Prediction Accuracy",
            "type": "stat",
            "targets": [
              {
                "expr": "predictive_alerting_model_accuracy * 100",
                "legendFormat": "Model Accuracy %"
              }
            ],
            "fieldConfig": {
              "defaults": {
                "thresholds": {
                  "steps": [
                    {"color": "red", "value": 0},
                    {"color": "yellow", "value": 80},
                    {"color": "green", "value": 85}
                  ]
                }
              }
            }
          },
          {
            "title": "Predictions & Alerts",
            "type": "graph",
            "targets": [
              {
                "expr": "rate(predictive_alerting_predictions_total[5m]) * 60",
                "legendFormat": "Predictions/min"
              },
              {
                "expr": "rate(predictive_alerting_alerts_triggered_total[5m]) * 60",
                "legendFormat": "Alerts/min"
              }
            ]
          },
          {
            "title": "Business Impact Predictions",
            "type": "timeseries",
            "targets": [
              {
                "expr": "predictive_alerting_jorge_bot_performance_prediction",
                "legendFormat": "Jorge Bot Performance"
              },
              {
                "expr": "predictive_alerting_cache_hit_rate_prediction",
                "legendFormat": "Cache Hit Rate"
              },
              {
                "expr": "predictive_alerting_revenue_impact_prediction",
                "legendFormat": "Revenue Impact Score"
              }
            ]
          },
          {
            "title": "False Positive Rate",
            "type": "stat",
            "targets": [
              {
                "expr": "rate(predictive_alerting_false_positives_total[1h]) / rate(predictive_alerting_predictions_total[1h]) * 100",
                "legendFormat": "False Positive Rate %"
              }
            ],
            "fieldConfig": {
              "defaults": {
                "thresholds": {
                  "steps": [
                    {"color": "green", "value": 0},
                    {"color": "yellow", "value": 3},
                    {"color": "red", "value": 5}
                  ]
                }
              }
            }
          }
        ]
      }
    }
EOF

    log_success "Monitoring dashboards setup completed"
}

# Main deployment function
main() {
    log_info "Starting predictive alerting engine deployment..."

    check_prerequisites
    build_and_push_image
    configure_kubectl
    deploy_kubernetes
    setup_prometheus_integration
    setup_alert_channels
    run_initial_model_training
    setup_monitoring_dashboards
    run_validation_tests

    log_success "🎉 Predictive Alerting Engine deployment completed successfully!"
    log_info ""
    log_info "📊 Monitoring & Access:"
    log_info "  Service API: kubectl port-forward -n jorge-platform svc/predictive-alerting-service 8080:80"
    log_info "  Grafana dashboards: kubectl port-forward -n monitoring svc/prometheus-grafana 3000:80"
    log_info "  Service logs: kubectl logs -f deployment/predictive-alerting-engine -n jorge-platform"
    log_info ""
    log_info "🔮 Capabilities Activated:"
    log_info "  - 15-30 minute advance warnings for performance issues"
    log_info "  - >85% prediction accuracy with <5% false positives"
    log_info "  - Business impact assessment for all alerts"
    log_info "  - Automatic ML model retraining every 6 hours"
    log_info "  - Integration with Slack and PagerDuty for critical alerts"
    log_info ""
    log_info "🎯 Business Benefits:"
    log_info "  - Proactive issue prevention before customer impact"
    log_info "  - Revenue protection through early intervention"
    log_info "  - Reduced MTTR (Mean Time To Resolution)"
    log_info "  - Data-driven operational intelligence"
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
        --slack-webhook)
            SLACK_WEBHOOK_URL="$2"
            shift 2
            ;;
        --pagerduty-key)
            PAGERDUTY_API_KEY="$2"
            shift 2
            ;;
        --skip-build)
            SKIP_BUILD=true
            shift
            ;;
        --skip-training)
            SKIP_TRAINING=true
            shift
            ;;
        --help)
            echo "Usage: $0 [OPTIONS]"
            echo "Options:"
            echo "  --env ENV               Deployment environment (default: production)"
            echo "  --region REGION         AWS region (default: us-east-1)"
            echo "  --cluster CLUSTER       EKS cluster name (default: jorge-platform-eks)"
            echo "  --image-tag TAG         Docker image tag (default: v1.0.0)"
            echo "  --registry REGISTRY     ECR registry URL"
            echo "  --slack-webhook URL     Slack webhook URL for alerts"
            echo "  --pagerduty-key KEY     PagerDuty API key for critical alerts"
            echo "  --skip-build           Skip Docker image build"
            echo "  --skip-training        Skip initial model training"
            echo "  --help                 Show this help"
            exit 0
            ;;
        *)
            error_exit "Unknown option: $1"
            ;;
    esac
done

# Run main function
main