#!/bin/bash

# Jorge Real Estate AI Platform - Development Startup Script
# Starts both backend and frontend for integrated development

set -e

echo "🚀 Starting Jorge Real Estate AI Platform..."
echo "=================================================="

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Function to check if a port is in use
check_port() {
    if lsof -Pi :$1 -sTCP:LISTEN -t >/dev/null ; then
        return 0
    else
        return 1
    fi
}

# Function to start backend
start_backend() {
    echo -e "${BLUE}🔧 Starting FastAPI Backend (Port 8000)...${NC}"

    if check_port 8000; then
        echo -e "${YELLOW}⚠️  Backend already running on port 8000${NC}"
    else
        cd ../
        if [ -f "app.py" ]; then
            echo "Starting FastAPI backend..."
            python app.py &
            BACKEND_PID=$!
            echo $BACKEND_PID > /tmp/jorge-backend.pid
            echo -e "${GREEN}✅ Backend started (PID: $BACKEND_PID)${NC}"
        else
            echo -e "${RED}❌ Backend app.py not found. Make sure you're in the correct directory.${NC}"
            exit 1
        fi
        cd enterprise-ui/
    fi
}

# Function to start frontend
start_frontend() {
    echo -e "${BLUE}🎨 Starting Next.js Frontend (Port 3000)...${NC}"

    if check_port 3000; then
        echo -e "${YELLOW}⚠️  Frontend already running on port 3000${NC}"
    else
        # Check if dependencies are installed
        if [ ! -d "node_modules" ]; then
            echo "Installing frontend dependencies..."
            npm install
        fi

        # Start development server
        npm run dev &
        FRONTEND_PID=$!
        echo $FRONTEND_PID > /tmp/jorge-frontend.pid
        echo -e "${GREEN}✅ Frontend started (PID: $FRONTEND_PID)${NC}"
    fi
}

# Function to setup environment
setup_environment() {
    echo -e "${BLUE}⚙️  Setting up environment...${NC}"

    if [ ! -f ".env.local" ]; then
        echo "Creating .env.local from .env.example..."
        cp .env.example .env.local
        echo -e "${GREEN}✅ Created .env.local${NC}"
        echo -e "${YELLOW}📝 You may want to edit .env.local with your specific configuration${NC}"
    fi
}

# Function to wait for services
wait_for_services() {
    echo -e "${BLUE}⏳ Waiting for services to start...${NC}"

    # Wait for backend
    echo "Checking backend health..."
    for i in {1..30}; do
        if curl -s http://localhost:8000/health >/dev/null 2>&1; then
            echo -e "${GREEN}✅ Backend is healthy${NC}"
            break
        fi
        if [ $i -eq 30 ]; then
            echo -e "${YELLOW}⚠️  Backend health check timed out, continuing anyway...${NC}"
        fi
        sleep 1
    done

    # Wait for frontend
    echo "Checking frontend..."
    for i in {1..30}; do
        if curl -s http://localhost:3000 >/dev/null 2>&1; then
            echo -e "${GREEN}✅ Frontend is ready${NC}"
            break
        fi
        if [ $i -eq 30 ]; then
            echo -e "${YELLOW}⚠️  Frontend check timed out, continuing anyway...${NC}"
        fi
        sleep 1
    done
}

# Function to display URLs
show_urls() {
    echo ""
    echo "🎉 Jorge Real Estate AI Platform is ready!"
    echo "=================================================="
    echo -e "${GREEN}📊 Jorge Command Center:${NC}    http://localhost:3000/jorge"
    echo -e "${GREEN}🏠 Platform Home:${NC}           http://localhost:3000"
    echo -e "${GREEN}📱 Field Agent Tools:${NC}       http://localhost:3000/field-agent"
    echo -e "${GREEN}🔧 Backend API:${NC}             http://localhost:8000"
    echo -e "${GREEN}📋 API Documentation:${NC}       http://localhost:8000/docs"
    echo ""
    echo -e "${BLUE}To stop the platform:${NC}"
    echo "  ./scripts/stop-jorge-platform.sh"
    echo ""
    echo -e "${YELLOW}Note: If you see connection errors, the frontend will automatically use mock data for development.${NC}"
    echo ""
}

# Main execution
main() {
    # Change to the enterprise-ui directory
    SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
    cd "$SCRIPT_DIR/.."

    setup_environment
    start_backend
    start_frontend
    wait_for_services
    show_urls

    # Keep script running
    echo "Press Ctrl+C to stop all services..."
    while true; do
        sleep 1
    done
}

# Trap Ctrl+C to cleanup
cleanup() {
    echo ""
    echo -e "${YELLOW}🛑 Stopping Jorge Platform...${NC}"

    if [ -f "/tmp/jorge-backend.pid" ]; then
        BACKEND_PID=$(cat /tmp/jorge-backend.pid)
        if kill -0 $BACKEND_PID 2>/dev/null; then
            kill $BACKEND_PID
            rm /tmp/jorge-backend.pid
            echo -e "${GREEN}✅ Backend stopped${NC}"
        fi
    fi

    if [ -f "/tmp/jorge-frontend.pid" ]; then
        FRONTEND_PID=$(cat /tmp/jorge-frontend.pid)
        if kill -0 $FRONTEND_PID 2>/dev/null; then
            kill $FRONTEND_PID
            rm /tmp/jorge-frontend.pid
            echo -e "${GREEN}✅ Frontend stopped${NC}"
        fi
    fi

    echo -e "${GREEN}👋 Jorge Platform stopped successfully${NC}"
    exit 0
}

trap cleanup INT TERM

# Check if we're in the right directory
if [ ! -f "package.json" ] || [ ! -f "next.config.ts" ]; then
    echo -e "${RED}❌ This script must be run from the enterprise-ui directory${NC}"
    echo "Current directory: $(pwd)"
    exit 1
fi

# Run main function
main