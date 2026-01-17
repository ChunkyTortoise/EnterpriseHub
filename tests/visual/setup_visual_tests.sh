#!/bin/bash
# ==============================================================================
# Visual Testing Setup Script
# ==============================================================================
# This script sets up the visual regression testing infrastructure for
# EnterpriseHub. It installs dependencies, configures Playwright, and
# captures initial baseline screenshots.
#
# Usage:
#   ./tests/visual/setup_visual_tests.sh
#
# Requirements:
#   - Python 3.11+
#   - pip
#   - Active internet connection
# ==============================================================================

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# ==============================================================================
# Helper Functions
# ==============================================================================

log_info() {
    echo -e "${BLUE}ℹ ${1}${NC}"
}

log_success() {
    echo -e "${GREEN}✓ ${1}${NC}"
}

log_warning() {
    echo -e "${YELLOW}⚠ ${1}${NC}"
}

log_error() {
    echo -e "${RED}✗ ${1}${NC}"
}

# ==============================================================================
# Pre-flight Checks
# ==============================================================================

log_info "Starting visual testing setup..."

# Check Python version
PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
log_info "Python version: $PYTHON_VERSION"

# Check if we're in the correct directory
if [ ! -f "requirements.txt" ]; then
    log_error "requirements.txt not found. Please run this script from the project root."
    exit 1
fi

# ==============================================================================
# Install Python Dependencies
# ==============================================================================

log_info "Installing Python dependencies..."

pip install -q -r requirements.txt

if [ $? -eq 0 ]; then
    log_success "Python dependencies installed"
else
    log_error "Failed to install Python dependencies"
    exit 1
fi

# ==============================================================================
# Install Playwright
# ==============================================================================

log_info "Installing Playwright browsers..."

playwright install chromium

if [ $? -eq 0 ]; then
    log_success "Playwright Chromium installed"
else
    log_error "Failed to install Playwright browsers"
    exit 1
fi

# Install system dependencies for Playwright
log_info "Installing Playwright system dependencies..."
playwright install-deps chromium || log_warning "Could not install system deps (may require sudo)"

# ==============================================================================
# Verify Installation
# ==============================================================================

log_info "Verifying installation..."

# Check pytest-playwright
python3 -c "import playwright" 2>/dev/null
if [ $? -eq 0 ]; then
    log_success "Playwright Python package installed"
else
    log_error "Playwright Python package not found"
    exit 1
fi

# Check axe-playwright
python3 -c "import axe_playwright" 2>/dev/null
if [ $? -eq 0 ]; then
    log_success "axe-playwright package installed"
else
    log_error "axe-playwright package not found"
    exit 1
fi

# ==============================================================================
# Create Snapshots Directory
# ==============================================================================

log_info "Creating snapshots directory..."

mkdir -p tests/visual/snapshots

log_success "Snapshots directory created"

# ==============================================================================
# Create .env if not exists
# ==============================================================================

if [ ! -f ".env" ]; then
    log_warning ".env file not found. Creating from .env.example..."
    if [ -f ".env.example" ]; then
        cp .env.example .env
        log_success ".env file created"
        log_warning "Please configure .env with your API keys before running tests"
    else
        log_error ".env.example not found. Please create .env manually"
    fi
fi

# ==============================================================================
# Start Streamlit App
# ==============================================================================

log_info "Setup complete! Next steps:"
echo ""
echo "1. Start the Streamlit app in one terminal:"
echo "   ${GREEN}streamlit run ghl_real_estate_ai/streamlit_demo/app.py${NC}"
echo ""
echo "2. In another terminal, capture baseline screenshots:"
echo "   ${GREEN}pytest tests/visual/test_component_snapshots.py --screenshot=on -v${NC}"
echo ""
echo "3. Run accessibility tests:"
echo "   ${GREEN}pytest tests/visual/test_accessibility.py -v${NC}"
echo ""
echo "4. View the README for more information:"
echo "   ${GREEN}cat tests/visual/README.md${NC}"
echo ""

log_success "Visual testing infrastructure ready!"

# ==============================================================================
# Optional: Start Streamlit in Background
# ==============================================================================

read -p "$(echo -e ${YELLOW}Would you like to start Streamlit now? [y/N]: ${NC})" -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    log_info "Starting Streamlit app..."

    # Start Streamlit in background
    DEMO_MODE=true streamlit run ghl_real_estate_ai/streamlit_demo/app.py \
        --server.port 8501 \
        --server.headless true \
        --server.address localhost &

    STREAMLIT_PID=$!
    echo $STREAMLIT_PID > .streamlit.pid

    log_info "Waiting for Streamlit to start..."

    # Wait for Streamlit to be ready
    timeout 60 bash -c 'until curl -s http://localhost:8501 > /dev/null; do sleep 2; done' || {
        log_error "Streamlit failed to start within 60 seconds"
        kill $STREAMLIT_PID 2>/dev/null || true
        rm .streamlit.pid
        exit 1
    }

    log_success "Streamlit started successfully (PID: $STREAMLIT_PID)"
    log_info "You can now run visual tests in this terminal"
    log_warning "To stop Streamlit: kill \$(cat .streamlit.pid)"

    echo ""
    read -p "$(echo -e ${YELLOW}Would you like to capture baseline screenshots now? [y/N]: ${NC})" -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        log_info "Capturing baseline screenshots..."

        pytest tests/visual/test_component_snapshots.py --screenshot=on -v

        if [ $? -eq 0 ]; then
            log_success "Baseline screenshots captured successfully!"
        else
            log_warning "Some tests may have failed. Review output above."
        fi
    fi
fi

log_success "All done! Happy testing!"
