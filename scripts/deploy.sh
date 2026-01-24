#!/bin/bash
# Jorge's Real Estate AI Platform - Automated Deployment Script
# Supports blue-green deployment, rollback, and zero-downtime deployments
# Author: Jorge Platform DevOps Team

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
DEPLOYMENT_LOG="/tmp/jorge-platform-deployment-$(date +%Y%m%d_%H%M%S).log"
COMPOSE_PROJECT_NAME="jorge-platform"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default values
ENVIRONMENT="staging"
STRATEGY="blue-green"
BACKEND_IMAGE=""
WORKER_IMAGE=""
TIMEOUT=300
DRY_RUN=false
FORCE=false

# Logging function
log() {
    local level=$1
    shift
    local message="$*"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')

    case $level in
        "INFO")
            echo -e "${GREEN}[INFO]${NC} ${timestamp} - $message" | tee -a "$DEPLOYMENT_LOG"
            ;;
        "WARN")
            echo -e "${YELLOW}[WARN]${NC} ${timestamp} - $message" | tee -a "$DEPLOYMENT_LOG"
            ;;
        "ERROR")
            echo -e "${RED}[ERROR]${NC} ${timestamp} - $message" | tee -a "$DEPLOYMENT_LOG"
            ;;
        "DEBUG")
            echo -e "${BLUE}[DEBUG]${NC} ${timestamp} - $message" | tee -a "$DEPLOYMENT_LOG"
            ;;
        *)
            echo "$timestamp - $message" | tee -a "$DEPLOYMENT_LOG"
            ;;
    esac
}

# Help function
show_help() {
    cat << EOF
Jorge Platform Deployment Script

Usage: $0 [OPTIONS]

Options:
    --backend-image IMAGE       Backend Docker image to deploy
    --worker-image IMAGE        Worker Docker image to deploy
    --environment ENV           Deployment environment (staging|production) [default: staging]
    --strategy STRATEGY         Deployment strategy (blue-green|rolling|recreate|rollback) [default: blue-green]
    --timeout SECONDS          Deployment timeout in seconds [default: 300]
    --dry-run                   Show what would be deployed without executing
    --force                     Force deployment even if health checks fail
    --help                      Show this help message

Examples:
    # Deploy to staging with blue-green strategy
    $0 --environment staging --strategy blue-green \\
       --backend-image ghcr.io/jorge/backend:v1.2.3 \\
       --worker-image ghcr.io/jorge/worker:v1.2.3

    # Deploy to production with rollback
    $0 --environment production --strategy rollback

    # Dry run to see what would be deployed
    $0 --dry-run --environment production \\
       --backend-image ghcr.io/jorge/backend:latest

Environment Variables:
    DEPLOYMENT_TOKEN            Required for production deployments
    PRODUCTION_HOST             Production host for SSH deployments
    DOCKER_REGISTRY_TOKEN       Token for private Docker registry

EOF
}

# Parse command line arguments
parse_args() {
    while [[ $# -gt 0 ]]; do
        case $1 in
            --backend-image)
                BACKEND_IMAGE="$2"
                shift 2
                ;;
            --worker-image)
                WORKER_IMAGE="$2"
                shift 2
                ;;
            --environment)
                ENVIRONMENT="$2"
                shift 2
                ;;
            --strategy)
                STRATEGY="$2"
                shift 2
                ;;
            --timeout)
                TIMEOUT="$2"
                shift 2
                ;;
            --dry-run)
                DRY_RUN=true
                shift
                ;;
            --force)
                FORCE=true
                shift
                ;;
            --help)
                show_help
                exit 0
                ;;
            *)
                log "ERROR" "Unknown option: $1"
                show_help
                exit 1
                ;;
        esac
    done
}

# Validate deployment configuration
validate_config() {
    log "INFO" "Validating deployment configuration..."

    # Check environment
    if [[ ! "$ENVIRONMENT" =~ ^(staging|production)$ ]]; then
        log "ERROR" "Invalid environment: $ENVIRONMENT. Must be 'staging' or 'production'"
        exit 1
    fi

    # Check strategy
    if [[ ! "$STRATEGY" =~ ^(blue-green|rolling|recreate|rollback)$ ]]; then
        log "ERROR" "Invalid strategy: $STRATEGY. Must be 'blue-green', 'rolling', 'recreate', or 'rollback'"
        exit 1
    fi

    # Check production requirements
    if [[ "$ENVIRONMENT" == "production" ]]; then
        if [[ -z "${DEPLOYMENT_TOKEN:-}" ]]; then
            log "ERROR" "DEPLOYMENT_TOKEN environment variable required for production deployments"
            exit 1
        fi

        if [[ "$STRATEGY" != "rollback" && -z "$BACKEND_IMAGE" ]]; then
            log "ERROR" "Backend image required for production deployments"
            exit 1
        fi
    fi

    # Check if images are provided for non-rollback deployments
    if [[ "$STRATEGY" != "rollback" && -z "$BACKEND_IMAGE" ]]; then
        log "WARN" "No backend image specified, using latest from registry"
        BACKEND_IMAGE="ghcr.io/jorge/real-estate-ai-backend:latest"
    fi

    if [[ "$STRATEGY" != "rollback" && -z "$WORKER_IMAGE" ]]; then
        log "WARN" "No worker image specified, using latest from registry"
        WORKER_IMAGE="ghcr.io/jorge/real-estate-ai-worker:latest"
    fi

    # Check Docker and Docker Compose
    if ! command -v docker &> /dev/null; then
        log "ERROR" "Docker is required but not installed"
        exit 1
    fi

    if ! command -v docker-compose &> /dev/null; then
        log "ERROR" "Docker Compose is required but not installed"
        exit 1
    fi

    log "INFO" "Configuration validation passed"
}

# Get current deployment info
get_current_deployment() {
    local current_containers
    current_containers=$(docker ps --filter "label=jorge.platform=true" --format "table {{.Names}}\t{{.Image}}\t{{.Status}}")

    if [[ -n "$current_containers" ]]; then
        log "INFO" "Current deployment:"
        echo "$current_containers" | tee -a "$DEPLOYMENT_LOG"
    else
        log "INFO" "No current deployment found"
    fi
}

# Create backup of current state
backup_current_state() {
    log "INFO" "Creating backup of current deployment state..."

    local backup_dir="/tmp/jorge-platform-backup-$(date +%Y%m%d_%H%M%S)"
    mkdir -p "$backup_dir"

    # Export current container configs
    docker ps --filter "label=jorge.platform=true" --format "{{.Names}}" | while read -r container; do
        if [[ -n "$container" ]]; then
            docker inspect "$container" > "${backup_dir}/${container}-config.json"
            log "DEBUG" "Backed up configuration for $container"
        fi
    done

    # Save compose file state
    if [[ -f "$PROJECT_ROOT/docker-compose.yml" ]]; then
        cp "$PROJECT_ROOT/docker-compose.yml" "${backup_dir}/"
    fi

    if [[ -f "$PROJECT_ROOT/docker-compose.scale.yml" ]]; then
        cp "$PROJECT_ROOT/docker-compose.scale.yml" "${backup_dir}/"
    fi

    echo "$backup_dir" > /tmp/jorge-platform-latest-backup
    log "INFO" "Backup created at: $backup_dir"
}

# Pull Docker images
pull_images() {
    log "INFO" "Pulling Docker images..."

    if [[ "$DRY_RUN" == "true" ]]; then
        log "INFO" "[DRY RUN] Would pull: $BACKEND_IMAGE"
        log "INFO" "[DRY RUN] Would pull: $WORKER_IMAGE"
        return 0
    fi

    # Login to registry if token is provided
    if [[ -n "${DOCKER_REGISTRY_TOKEN:-}" ]]; then
        echo "$DOCKER_REGISTRY_TOKEN" | docker login ghcr.io -u "$GITHUB_ACTOR" --password-stdin
    fi

    # Pull backend image
    log "INFO" "Pulling backend image: $BACKEND_IMAGE"
    docker pull "$BACKEND_IMAGE" || {
        log "ERROR" "Failed to pull backend image: $BACKEND_IMAGE"
        exit 1
    }

    # Pull worker image
    log "INFO" "Pulling worker image: $WORKER_IMAGE"
    docker pull "$WORKER_IMAGE" || {
        log "ERROR" "Failed to pull worker image: $WORKER_IMAGE"
        exit 1
    }

    log "INFO" "Successfully pulled all images"
}

# Health check function
health_check() {
    local service_name=$1
    local health_url=$2
    local max_attempts=30
    local attempt=1

    log "INFO" "Starting health check for $service_name at $health_url"

    while [[ $attempt -le $max_attempts ]]; do
        if curl -f -s "$health_url" > /dev/null; then
            log "INFO" "Health check passed for $service_name (attempt $attempt/$max_attempts)"
            return 0
        fi

        log "DEBUG" "Health check attempt $attempt/$max_attempts failed for $service_name"
        sleep 5
        ((attempt++))
    done

    log "ERROR" "Health check failed for $service_name after $max_attempts attempts"
    return 1
}

# Blue-green deployment strategy
deploy_blue_green() {
    log "INFO" "Starting blue-green deployment..."

    local compose_file="docker-compose.scale.yml"
    if [[ "$ENVIRONMENT" == "staging" ]]; then
        compose_file="docker-compose.yml"
    fi

    # Determine current and next colors
    local current_color=""
    local next_color=""

    if docker ps --filter "label=jorge.color=blue" --filter "status=running" | grep -q jorge; then
        current_color="blue"
        next_color="green"
    else
        current_color="green"
        next_color="blue"
    fi

    log "INFO" "Current deployment: $current_color, deploying to: $next_color"

    if [[ "$DRY_RUN" == "true" ]]; then
        log "INFO" "[DRY RUN] Would deploy $next_color environment with:"
        log "INFO" "[DRY RUN]   Backend: $BACKEND_IMAGE"
        log "INFO" "[DRY RUN]   Worker: $WORKER_IMAGE"
        log "INFO" "[DRY RUN]   Compose file: $compose_file"
        return 0
    fi

    # Create temporary compose file with new images and color
    local temp_compose="/tmp/jorge-deploy-${next_color}.yml"
    sed "s|jorge/real-estate-ai-backend:.*|${BACKEND_IMAGE}|g; s|jorge/real-estate-ai-worker:.*|${WORKER_IMAGE}|g" "$PROJECT_ROOT/$compose_file" > "$temp_compose"

    # Add color labels
    sed -i.bak "s/labels:/labels:\n      - jorge.color=${next_color}/g" "$temp_compose"

    # Start new environment
    log "INFO" "Starting $next_color environment..."
    COMPOSE_PROJECT_NAME="${COMPOSE_PROJECT_NAME}-${next_color}" \
    docker-compose -f "$temp_compose" up -d

    # Wait for services to be ready
    log "INFO" "Waiting for services to be ready..."
    sleep 30

    # Health check new environment
    local api_port
    if [[ "$next_color" == "blue" ]]; then
        api_port="8000"
    else
        api_port="8001"  # Green environment on different port
    fi

    if ! health_check "Jorge API ($next_color)" "http://localhost:${api_port}/health"; then
        log "ERROR" "Health check failed for new $next_color environment"

        if [[ "$FORCE" != "true" ]]; then
            log "INFO" "Rolling back $next_color environment..."
            COMPOSE_PROJECT_NAME="${COMPOSE_PROJECT_NAME}-${next_color}" \
            docker-compose -f "$temp_compose" down
            rm -f "$temp_compose"
            exit 1
        else
            log "WARN" "Forcing deployment despite health check failure"
        fi
    fi

    # Switch traffic to new environment (update load balancer)
    log "INFO" "Switching traffic to $next_color environment..."

    # Update Nginx configuration
    if [[ -f "$PROJECT_ROOT/nginx/nginx.conf" ]]; then
        sed -i.bak "s/jorge-platform-api-[0-9]*/jorge-platform-${next_color}-api/g" "$PROJECT_ROOT/nginx/nginx.conf"
        docker exec jorge-platform-nginx nginx -s reload || log "WARN" "Failed to reload Nginx configuration"
    fi

    # Health check after traffic switch
    sleep 10
    if ! health_check "Jorge API (after switch)" "http://localhost/api/health"; then
        log "ERROR" "Health check failed after traffic switch"

        if [[ "$FORCE" != "true" ]]; then
            log "INFO" "Rolling back traffic to $current_color..."
            # Restore Nginx config
            if [[ -f "$PROJECT_ROOT/nginx/nginx.conf.bak" ]]; then
                mv "$PROJECT_ROOT/nginx/nginx.conf.bak" "$PROJECT_ROOT/nginx/nginx.conf"
                docker exec jorge-platform-nginx nginx -s reload
            fi
            exit 1
        fi
    fi

    # Stop old environment after successful deployment
    log "INFO" "Stopping old $current_color environment..."
    COMPOSE_PROJECT_NAME="${COMPOSE_PROJECT_NAME}-${current_color}" \
    docker-compose down || log "WARN" "Failed to stop old environment"

    # Clean up
    rm -f "$temp_compose"

    log "INFO" "Blue-green deployment completed successfully"
    log "INFO" "Active environment: $next_color"
    log "INFO" "Backend: $BACKEND_IMAGE"
    log "INFO" "Worker: $WORKER_IMAGE"
}

# Rolling deployment strategy
deploy_rolling() {
    log "INFO" "Starting rolling deployment..."

    local compose_file="docker-compose.scale.yml"
    if [[ "$ENVIRONMENT" == "staging" ]]; then
        compose_file="docker-compose.yml"
    fi

    if [[ "$DRY_RUN" == "true" ]]; then
        log "INFO" "[DRY RUN] Would perform rolling update with $compose_file"
        return 0
    fi

    # Update images in compose file
    local temp_compose="/tmp/jorge-rolling-deploy.yml"
    sed "s|jorge/real-estate-ai-backend:.*|${BACKEND_IMAGE}|g; s|jorge/real-estate-ai-worker:.*|${WORKER_IMAGE}|g" "$PROJECT_ROOT/$compose_file" > "$temp_compose"

    # Perform rolling update
    log "INFO" "Performing rolling update..."
    docker-compose -f "$temp_compose" up -d --no-deps --scale jorge-api=2

    # Health check
    if ! health_check "Jorge API (rolling)" "http://localhost:8000/health"; then
        log "ERROR" "Rolling deployment health check failed"
        exit 1
    fi

    # Scale back to normal
    docker-compose -f "$temp_compose" up -d --scale jorge-api=1

    rm -f "$temp_compose"
    log "INFO" "Rolling deployment completed successfully"
}

# Recreate deployment strategy
deploy_recreate() {
    log "INFO" "Starting recreate deployment..."

    local compose_file="docker-compose.scale.yml"
    if [[ "$ENVIRONMENT" == "staging" ]]; then
        compose_file="docker-compose.yml"
    fi

    if [[ "$DRY_RUN" == "true" ]]; then
        log "INFO" "[DRY RUN] Would recreate all services with $compose_file"
        return 0
    fi

    # Stop all services
    log "INFO" "Stopping all services..."
    docker-compose -f "$PROJECT_ROOT/$compose_file" down

    # Update images in compose file
    local temp_compose="/tmp/jorge-recreate-deploy.yml"
    sed "s|jorge/real-estate-ai-backend:.*|${BACKEND_IMAGE}|g; s|jorge/real-estate-ai-worker:.*|${WORKER_IMAGE}|g" "$PROJECT_ROOT/$compose_file" > "$temp_compose"

    # Start all services
    log "INFO" "Starting all services with new images..."
    docker-compose -f "$temp_compose" up -d

    # Wait and health check
    sleep 30
    if ! health_check "Jorge API (recreate)" "http://localhost:8000/health"; then
        log "ERROR" "Recreate deployment health check failed"
        exit 1
    fi

    rm -f "$temp_compose"
    log "INFO" "Recreate deployment completed successfully"
}

# Rollback to previous deployment
rollback_deployment() {
    log "INFO" "Starting deployment rollback..."

    if [[ ! -f "/tmp/jorge-platform-latest-backup" ]]; then
        log "ERROR" "No backup found for rollback. Cannot proceed."
        exit 1
    fi

    local backup_dir=$(cat /tmp/jorge-platform-latest-backup)

    if [[ ! -d "$backup_dir" ]]; then
        log "ERROR" "Backup directory not found: $backup_dir"
        exit 1
    fi

    if [[ "$DRY_RUN" == "true" ]]; then
        log "INFO" "[DRY RUN] Would rollback to state from: $backup_dir"
        return 0
    fi

    log "INFO" "Rolling back to previous deployment state..."

    # Stop current services
    docker-compose -f "$PROJECT_ROOT/docker-compose.yml" down || true
    docker-compose -f "$PROJECT_ROOT/docker-compose.scale.yml" down || true

    # Restore compose files
    if [[ -f "$backup_dir/docker-compose.yml" ]]; then
        cp "$backup_dir/docker-compose.yml" "$PROJECT_ROOT/"
    fi

    if [[ -f "$backup_dir/docker-compose.scale.yml" ]]; then
        cp "$backup_dir/docker-compose.scale.yml" "$PROJECT_ROOT/"
    fi

    # Start services with previous configuration
    local compose_file="docker-compose.scale.yml"
    if [[ "$ENVIRONMENT" == "staging" ]]; then
        compose_file="docker-compose.yml"
    fi

    docker-compose -f "$PROJECT_ROOT/$compose_file" up -d

    # Health check rollback
    sleep 30
    if ! health_check "Jorge API (rollback)" "http://localhost:8000/health"; then
        log "ERROR" "Rollback health check failed"
        exit 1
    fi

    log "INFO" "Rollback completed successfully"
}

# Post-deployment validation
post_deployment_validation() {
    log "INFO" "Running post-deployment validation..."

    # Check core services
    local services=("jorge-api" "jorge-worker" "redis" "postgres")

    for service in "${services[@]}"; do
        if ! docker ps --filter "name=$service" --filter "status=running" | grep -q "$service"; then
            log "ERROR" "Service $service is not running"
            return 1
        fi
        log "INFO" "Service $service is running"
    done

    # Check API endpoints
    local endpoints=(
        "/health"
        "/api/jorge-seller/health"
        "/api/lead-bot/health"
        "/api/intent-decoder/health"
    )

    for endpoint in "${endpoints[@]}"; do
        if health_check "Endpoint $endpoint" "http://localhost:8000$endpoint"; then
            log "INFO" "Endpoint $endpoint is healthy"
        else
            log "ERROR" "Endpoint $endpoint is unhealthy"
            return 1
        fi
    done

    log "INFO" "Post-deployment validation completed successfully"
}

# Cleanup function
cleanup() {
    local exit_code=$?

    if [[ $exit_code -ne 0 ]]; then
        log "ERROR" "Deployment failed with exit code $exit_code"

        # Save failure logs
        local failure_log="/tmp/jorge-platform-deployment-failure-$(date +%Y%m%d_%H%M%S).log"
        cp "$DEPLOYMENT_LOG" "$failure_log"
        log "ERROR" "Failure logs saved to: $failure_log"
    else
        log "INFO" "Deployment completed successfully"
    fi

    # Clean up temporary files
    rm -f /tmp/jorge-deploy-*.yml
    rm -f /tmp/jorge-rolling-deploy.yml
    rm -f /tmp/jorge-recreate-deploy.yml

    exit $exit_code
}

# Main deployment function
main() {
    trap cleanup EXIT

    log "INFO" "Starting Jorge Platform deployment"
    log "INFO" "Environment: $ENVIRONMENT"
    log "INFO" "Strategy: $STRATEGY"
    log "INFO" "Logs: $DEPLOYMENT_LOG"

    parse_args "$@"
    validate_config

    # Get current state
    get_current_deployment

    # Create backup unless rollback
    if [[ "$STRATEGY" != "rollback" ]]; then
        backup_current_state
        pull_images
    fi

    # Execute deployment strategy
    case $STRATEGY in
        "blue-green")
            deploy_blue_green
            ;;
        "rolling")
            deploy_rolling
            ;;
        "recreate")
            deploy_recreate
            ;;
        "rollback")
            rollback_deployment
            ;;
        *)
            log "ERROR" "Unknown deployment strategy: $STRATEGY"
            exit 1
            ;;
    esac

    # Post-deployment validation
    if [[ "$DRY_RUN" != "true" && "$STRATEGY" != "rollback" ]]; then
        post_deployment_validation
    fi

    log "INFO" "Jorge Platform deployment completed successfully"
    log "INFO" "Deployment logs available at: $DEPLOYMENT_LOG"
}

# Run main function with all arguments
main "$@"