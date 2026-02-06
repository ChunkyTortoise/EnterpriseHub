#!/bin/bash

# Jorge Real Estate AI Platform - Stop Script
# Cleanly stops both backend and frontend services

set -e

echo "🛑 Stopping Jorge Real Estate AI Platform..."

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Function to stop a service by PID file
stop_service() {
    local service_name=$1
    local pid_file=$2

    if [ -f "$pid_file" ]; then
        PID=$(cat $pid_file)
        if kill -0 $PID 2>/dev/null; then
            kill $PID
            rm $pid_file
            echo -e "${GREEN}✅ $service_name stopped (PID: $PID)${NC}"
        else
            rm $pid_file
            echo -e "${YELLOW}⚠️  $service_name was not running${NC}"
        fi
    else
        echo -e "${YELLOW}⚠️  $service_name PID file not found${NC}"
    fi
}

# Function to kill processes by port
kill_by_port() {
    local port=$1
    local service_name=$2

    PID=$(lsof -ti:$port 2>/dev/null || echo "")
    if [ ! -z "$PID" ]; then
        kill -9 $PID 2>/dev/null || true
        echo -e "${GREEN}✅ Killed $service_name on port $port (PID: $PID)${NC}"
    fi
}

# Stop services by PID files first
stop_service "Backend" "/tmp/jorge-backend.pid"
stop_service "Frontend" "/tmp/jorge-frontend.pid"

# Fallback: kill by port
echo -e "${BLUE}🔍 Checking for remaining processes...${NC}"
kill_by_port 8000 "Backend"
kill_by_port 3000 "Frontend"

# Clean up any remaining Jorge-related processes
echo -e "${BLUE}🧹 Cleaning up any remaining processes...${NC}"

# Kill any python processes running app.py (backend)
pkill -f "python.*app.py" 2>/dev/null || true

# Kill any node processes running next dev (frontend)
pkill -f "next dev" 2>/dev/null || true

echo -e "${GREEN}✅ Jorge Real Estate AI Platform stopped successfully${NC}"
echo ""
echo -e "${BLUE}To restart the platform:${NC}"
echo "  ./scripts/start-jorge-platform.sh"
echo ""