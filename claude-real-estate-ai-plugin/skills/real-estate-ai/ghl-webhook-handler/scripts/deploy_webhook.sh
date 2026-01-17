#!/bin/bash
"""
GHL Webhook Deployment Script
Automated deployment for real estate webhook handlers

This script handles:
- Environment setup
- Dependency installation
- Security configuration
- Service deployment
- Health checks
"""

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PROJECT_NAME="ghl-webhook-handler"
PYTHON_VERSION="3.11"
SERVICE_PORT="${PORT:-8000}"
ENVIRONMENT="${ENV:-production}"

echo -e "${BLUE}🚀 Deploying GHL Webhook Handler${NC}"
echo -e "${BLUE}Environment: ${ENVIRONMENT}${NC}"
echo -e "${BLUE}Port: ${SERVICE_PORT}${NC}"
echo ""

# Function to print status
print_status() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Check if running as root
if [[ $EUID -eq 0 ]]; then
    print_error "This script should not be run as root for security reasons"
    exit 1
fi

# Validate required environment variables
validate_env() {
    echo "🔍 Validating environment variables..."

    required_vars=(
        "GHL_WEBHOOK_SECRET"
        "GHL_API_KEY"
        "ANTHROPIC_API_KEY"
    )

    missing_vars=()

    for var in "${required_vars[@]}"; do
        if [[ -z "${!var}" ]]; then
            missing_vars+=($var)
        fi
    done

    if [[ ${#missing_vars[@]} -ne 0 ]]; then
        print_error "Missing required environment variables:"
        for var in "${missing_vars[@]}"; do
            echo -e "${RED}  - $var${NC}"
        done
        echo ""
        echo "Please set these variables and try again:"
        echo "export GHL_WEBHOOK_SECRET='your_webhook_secret'"
        echo "export GHL_API_KEY='your_ghl_api_key'"
        echo "export ANTHROPIC_API_KEY='your_anthropic_key'"
        exit 1
    fi

    print_status "All required environment variables are set"
}

# Check Python version
check_python() {
    echo "🐍 Checking Python version..."

    if ! command -v python3 &> /dev/null; then
        print_error "Python 3 is not installed"
        exit 1
    fi

    python_version=$(python3 --version | cut -d' ' -f2)
    major_version=$(echo $python_version | cut -d'.' -f1)
    minor_version=$(echo $python_version | cut -d'.' -f2)

    if [[ $major_version -lt 3 ]] || [[ $major_version -eq 3 && $minor_version -lt 8 ]]; then
        print_error "Python 3.8+ is required (found $python_version)"
        exit 1
    fi

    print_status "Python $python_version is compatible"
}

# Create virtual environment
setup_venv() {
    echo "📦 Setting up virtual environment..."

    if [[ ! -d "venv" ]]; then
        python3 -m venv venv
        print_status "Created virtual environment"
    else
        print_status "Virtual environment already exists"
    fi

    source venv/bin/activate

    # Upgrade pip
    pip install --upgrade pip > /dev/null 2>&1
    print_status "Updated pip"
}

# Install dependencies
install_deps() {
    echo "📚 Installing dependencies..."

    # Create requirements.txt if it doesn't exist
    if [[ ! -f "requirements.txt" ]]; then
        cat > requirements.txt << EOF
fastapi==0.104.1
uvicorn[standard]==0.24.0
pydantic==2.5.0
httpx==0.25.2
anthropic==0.8.0
redis==5.0.1
python-multipart==0.0.6
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
python-dotenv==1.0.0
prometheus-client==0.19.0
structlog==23.2.0
EOF
        print_status "Created requirements.txt"
    fi

    pip install -r requirements.txt
    print_status "Installed Python dependencies"
}

# Setup configuration
setup_config() {
    echo "⚙️  Setting up configuration..."

    # Create .env file for local development
    if [[ ! -f ".env" && "$ENVIRONMENT" == "development" ]]; then
        cat > .env << EOF
# GHL Configuration
GHL_WEBHOOK_SECRET=${GHL_WEBHOOK_SECRET}
GHL_API_KEY=${GHL_API_KEY}
GHL_API_BASE_URL=https://rest.gohighlevel.com/v1

# AI Configuration
ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}

# Application Configuration
PORT=${SERVICE_PORT}
HOST=0.0.0.0
DEBUG=false
LOG_LEVEL=info

# Security Configuration
RATE_LIMIT_PER_MINUTE=60
MAX_REQUEST_SIZE=1048576

# Redis Configuration (optional)
REDIS_URL=redis://localhost:6379/0

# Monitoring Configuration
ENABLE_METRICS=true
METRICS_PORT=9090
EOF
        print_status "Created .env configuration file"
    fi

    # Validate webhook secret strength
    if [[ ${#GHL_WEBHOOK_SECRET} -lt 32 ]]; then
        print_warning "Webhook secret should be at least 32 characters for security"
    fi
}

# Run tests
run_tests() {
    echo "🧪 Running tests..."

    if [[ -f "test_webhook.py" ]]; then
        python -m pytest test_webhook.py -v
        print_status "All tests passed"
    else
        print_warning "No tests found (consider adding test_webhook.py)"
    fi
}

# Check health endpoint
health_check() {
    echo "🏥 Performing health check..."

    # Start the service in background
    python complete_webhook_handler.py &
    SERVICE_PID=$!

    # Wait for service to start
    sleep 5

    # Check if service is responding
    if curl -f -s "http://localhost:${SERVICE_PORT}/" > /dev/null; then
        print_status "Service is responding on port ${SERVICE_PORT}"

        # Test webhook endpoint
        response=$(curl -s -X POST "http://localhost:${SERVICE_PORT}/webhook/ghl" \
            -H "Content-Type: application/json" \
            -d '{"contactId": "test", "locationId": "test"}' \
            -w "%{http_code}")

        if [[ "$response" =~ "401" ]]; then
            print_status "Webhook security is working (401 unauthorized as expected)"
        fi

    else
        print_error "Service is not responding"
        kill $SERVICE_PID 2>/dev/null || true
        exit 1
    fi

    # Clean up
    kill $SERVICE_PID 2>/dev/null || true
    sleep 2
}

# Setup systemd service (Linux only)
setup_systemd() {
    if [[ "$ENVIRONMENT" == "production" && "$OSTYPE" == "linux-gnu"* ]]; then
        echo "🔧 Setting up systemd service..."

        service_file="/etc/systemd/system/${PROJECT_NAME}.service"

        if [[ -w "/etc/systemd/system/" ]]; then
            cat > $service_file << EOF
[Unit]
Description=GHL Real Estate Webhook Handler
After=network.target

[Service]
Type=simple
User=$(whoami)
WorkingDirectory=$(pwd)
Environment=PATH=$(pwd)/venv/bin
ExecStart=$(pwd)/venv/bin/python complete_webhook_handler.py
Restart=always
RestartSec=3
StandardOutput=journal
StandardError=journal
SyslogIdentifier=${PROJECT_NAME}

# Security settings
NoNewPrivileges=yes
PrivateTmp=yes
ProtectSystem=strict
ProtectHome=yes
ReadWritePaths=$(pwd)

# Environment variables
Environment=GHL_WEBHOOK_SECRET=${GHL_WEBHOOK_SECRET}
Environment=GHL_API_KEY=${GHL_API_KEY}
Environment=ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
Environment=PORT=${SERVICE_PORT}

[Install]
WantedBy=multi-user.target
EOF

            sudo systemctl daemon-reload
            sudo systemctl enable ${PROJECT_NAME}
            print_status "Systemd service configured"
        else
            print_warning "Cannot write systemd service (insufficient permissions)"
        fi
    fi
}

# Setup Docker (optional)
setup_docker() {
    if [[ -f "Dockerfile" && "$ENVIRONMENT" == "production" ]]; then
        echo "🐳 Setting up Docker deployment..."

        docker build -t ${PROJECT_NAME}:latest .
        print_status "Docker image built"

        # Create docker-compose.yml if it doesn't exist
        if [[ ! -f "docker-compose.yml" ]]; then
            cat > docker-compose.yml << EOF
version: '3.8'

services:
  webhook:
    build: .
    ports:
      - "${SERVICE_PORT}:8000"
    environment:
      - GHL_WEBHOOK_SECRET=${GHL_WEBHOOK_SECRET}
      - GHL_API_KEY=${GHL_API_KEY}
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
      - PORT=8000
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - redis
    restart: unless-stopped

  redis:
    image: redis:7-alpine
    restart: unless-stopped
    volumes:
      - redis_data:/data

volumes:
  redis_data:
EOF
            print_status "Created docker-compose.yml"
        fi
    fi
}

# Main deployment function
deploy() {
    echo "🚀 Starting deployment process..."
    echo ""

    validate_env
    check_python
    setup_venv
    install_deps
    setup_config

    if [[ "$ENVIRONMENT" == "development" ]]; then
        run_tests
        health_check
    fi

    setup_systemd
    setup_docker

    echo ""
    print_status "🎉 Deployment completed successfully!"
    echo ""
    echo "Next steps:"
    echo "1. Configure your GHL webhook URL to point to:"
    echo "   https://your-domain.com/webhook/ghl"
    echo ""
    echo "2. Start the service:"
    if [[ "$ENVIRONMENT" == "production" && "$OSTYPE" == "linux-gnu"* ]]; then
        echo "   sudo systemctl start ${PROJECT_NAME}"
        echo "   sudo systemctl status ${PROJECT_NAME}"
    else
        echo "   source venv/bin/activate"
        echo "   python complete_webhook_handler.py"
    fi
    echo ""
    echo "3. Monitor logs and analytics at:"
    echo "   http://your-domain:${SERVICE_PORT}/analytics/qualification"
    echo ""
    echo "4. Test the webhook with a sample payload"
}

# Handle command line arguments
case "${1:-deploy}" in
    "deploy")
        deploy
        ;;
    "validate")
        validate_env
        print_status "Environment validation passed"
        ;;
    "health")
        health_check
        ;;
    "config")
        setup_config
        print_status "Configuration setup completed"
        ;;
    "help")
        echo "Usage: $0 [deploy|validate|health|config|help]"
        echo ""
        echo "Commands:"
        echo "  deploy   - Full deployment (default)"
        echo "  validate - Validate environment variables"
        echo "  health   - Run health check"
        echo "  config   - Setup configuration only"
        echo "  help     - Show this help"
        ;;
    *)
        print_error "Unknown command: $1"
        echo "Use '$0 help' for usage information"
        exit 1
        ;;
esac