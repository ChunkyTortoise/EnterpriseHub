#!/bin/bash

# Jorge's Real Estate AI - Demo Services Launcher
# ===============================================
#
# Automated script to launch all required services for client demonstrations
# with optimal configuration for performance and stability.
#
# Usage: ./launch_demo_services.sh [--stop] [--status] [--restart]

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m' # No Color

# Service configuration
FASTAPI_PORT=8002
STREAMLIT_MAIN_PORT=8501
STREAMLIT_JORGE_PORT=8503

# Log file locations
LOG_DIR="demo_logs"
mkdir -p "$LOG_DIR"

FASTAPI_LOG="$LOG_DIR/fastapi_demo.log"
STREAMLIT_MAIN_LOG="$LOG_DIR/streamlit_main_demo.log"
STREAMLIT_JORGE_LOG="$LOG_DIR/streamlit_jorge_demo.log"

# PID file locations for process management
PID_DIR="demo_pids"
mkdir -p "$PID_DIR"

FASTAPI_PID="$PID_DIR/fastapi.pid"
STREAMLIT_MAIN_PID="$PID_DIR/streamlit_main.pid"
STREAMLIT_JORGE_PID="$PID_DIR/streamlit_jorge.pid"

print_header() {
    echo -e "${PURPLE}"
    echo "🎯 Jorge's Real Estate AI - Demo Services Launcher"
    echo "=================================================="
    echo -e "${NC}"
}

print_status() {
    local message="$1"
    local type="${2:-info}"

    case $type in
        "success") echo -e "${GREEN}✅ $message${NC}" ;;
        "error")   echo -e "${RED}❌ $message${NC}" ;;
        "warning") echo -e "${YELLOW}⚠️  $message${NC}" ;;
        "info")    echo -e "${BLUE}ℹ️  $message${NC}" ;;
        *)         echo "$message" ;;
    esac
}

check_dependencies() {
    print_status "Checking dependencies..." "info"

    # Check Python 3
    if ! command -v python3 &> /dev/null; then
        print_status "Python 3 is required but not installed" "error"
        exit 1
    fi

    # Check required Python modules
    if ! python3 -c "import streamlit, fastapi, uvicorn" 2>/dev/null; then
        print_status "Required Python modules missing. Install requirements.txt" "error"
        exit 1
    fi

    print_status "All dependencies satisfied" "success"
}

check_ports() {
    local ports=($FASTAPI_PORT $STREAMLIT_MAIN_PORT $STREAMLIT_JORGE_PORT)
    local port_names=("FastAPI" "Streamlit Main" "Streamlit Jorge")

    print_status "Checking port availability..." "info"

    for i in "${!ports[@]}"; do
        local port=${ports[$i]}
        local name=${port_names[$i]}

        if lsof -ti:$port >/dev/null 2>&1; then
            print_status "Port $port ($name) is already in use" "warning"
        else
            print_status "Port $port ($name) is available" "success"
        fi
    done
}

start_fastapi() {
    print_status "Starting FastAPI backend..." "info"

    if [[ -f $FASTAPI_PID ]] && kill -0 "$(cat $FASTAPI_PID)" 2>/dev/null; then
        print_status "FastAPI is already running (PID: $(cat $FASTAPI_PID))" "warning"
        return
    fi

    # Start FastAPI with optimized settings for demo
    cd ghl_real_estate_ai/api
    nohup python3 -m uvicorn main:app \
        --host 0.0.0.0 \
        --port $FASTAPI_PORT \
        --reload \
        --access-log \
        --log-level info > "../../$FASTAPI_LOG" 2>&1 &

    local pid=$!
    echo $pid > "../../$FASTAPI_PID"
    cd - > /dev/null

    # Wait for service to start
    sleep 3
    if kill -0 $pid 2>/dev/null; then
        print_status "FastAPI started successfully (PID: $pid, Port: $FASTAPI_PORT)" "success"
    else
        print_status "FastAPI failed to start. Check $FASTAPI_LOG" "error"
        return 1
    fi
}

start_streamlit_main() {
    print_status "Starting Main Streamlit Dashboard..." "info"

    if [[ -f $STREAMLIT_MAIN_PID ]] && kill -0 "$(cat $STREAMLIT_MAIN_PID)" 2>/dev/null; then
        print_status "Main Dashboard is already running (PID: $(cat $STREAMLIT_MAIN_PID))" "warning"
        return
    fi

    # Start main Streamlit app with demo-optimized settings
    nohup python3 -m streamlit run ghl_real_estate_ai/streamlit_demo/app.py \
        --server.port $STREAMLIT_MAIN_PORT \
        --server.headless true \
        --server.runOnSave false \
        --server.address 0.0.0.0 \
        --browser.gatherUsageStats false > "$STREAMLIT_MAIN_LOG" 2>&1 &

    local pid=$!
    echo $pid > "$STREAMLIT_MAIN_PID"

    # Wait for service to start
    sleep 5
    if kill -0 $pid 2>/dev/null; then
        print_status "Main Dashboard started successfully (PID: $pid, Port: $STREAMLIT_MAIN_PORT)" "success"
    else
        print_status "Main Dashboard failed to start. Check $STREAMLIT_MAIN_LOG" "error"
        return 1
    fi
}

start_streamlit_jorge() {
    print_status "Starting Jorge Command Center..." "info"

    if [[ -f $STREAMLIT_JORGE_PID ]] && kill -0 "$(cat $STREAMLIT_JORGE_PID)" 2>/dev/null; then
        print_status "Jorge Command Center is already running (PID: $(cat $STREAMLIT_JORGE_PID))" "warning"
        return
    fi

    # Start Jorge Command Center with demo-optimized settings
    nohup python3 -m streamlit run ghl_real_estate_ai/streamlit_demo/jorge_bot_command_center.py \
        --server.port $STREAMLIT_JORGE_PORT \
        --server.headless true \
        --server.runOnSave false \
        --server.address 0.0.0.0 \
        --browser.gatherUsageStats false > "$STREAMLIT_JORGE_LOG" 2>&1 &

    local pid=$!
    echo $pid > "$STREAMLIT_JORGE_PID"

    # Wait for service to start
    sleep 5
    if kill -0 $pid 2>/dev/null; then
        print_status "Jorge Command Center started successfully (PID: $pid, Port: $STREAMLIT_JORGE_PORT)" "success"
    else
        print_status "Jorge Command Center failed to start. Check $STREAMLIT_JORGE_LOG" "error"
        return 1
    fi
}

stop_service() {
    local service_name="$1"
    local pid_file="$2"

    if [[ -f "$pid_file" ]]; then
        local pid=$(cat "$pid_file")
        if kill -0 "$pid" 2>/dev/null; then
            kill "$pid"
            rm -f "$pid_file"
            print_status "$service_name stopped (PID: $pid)" "success"
        else
            print_status "$service_name was not running" "warning"
            rm -f "$pid_file"
        fi
    else
        print_status "$service_name PID file not found" "warning"
    fi
}

stop_all_services() {
    print_status "Stopping all demo services..." "info"

    stop_service "FastAPI" "$FASTAPI_PID"
    stop_service "Main Dashboard" "$STREAMLIT_MAIN_PID"
    stop_service "Jorge Command Center" "$STREAMLIT_JORGE_PID"

    # Also kill any remaining processes on our ports
    for port in $FASTAPI_PORT $STREAMLIT_MAIN_PORT $STREAMLIT_JORGE_PORT; do
        if lsof -ti:$port >/dev/null 2>&1; then
            print_status "Force killing process on port $port" "warning"
            lsof -ti:$port | xargs kill -9 2>/dev/null || true
        fi
    done
}

show_service_status() {
    print_status "Checking service status..." "info"
    echo

    # FastAPI
    if [[ -f $FASTAPI_PID ]] && kill -0 "$(cat $FASTAPI_PID)" 2>/dev/null; then
        print_status "FastAPI Backend: RUNNING (Port: $FASTAPI_PORT, PID: $(cat $FASTAPI_PID))" "success"
    else
        print_status "FastAPI Backend: STOPPED" "error"
    fi

    # Main Dashboard
    if [[ -f $STREAMLIT_MAIN_PID ]] && kill -0 "$(cat $STREAMLIT_MAIN_PID)" 2>/dev/null; then
        print_status "Main Dashboard: RUNNING (Port: $STREAMLIT_MAIN_PORT, PID: $(cat $STREAMLIT_MAIN_PID))" "success"
    else
        print_status "Main Dashboard: STOPPED" "error"
    fi

    # Jorge Command Center
    if [[ -f $STREAMLIT_JORGE_PID ]] && kill -0 "$(cat $STREAMLIT_JORGE_PID)" 2>/dev/null; then
        print_status "Jorge Command Center: RUNNING (Port: $STREAMLIT_JORGE_PORT, PID: $(cat $STREAMLIT_JORGE_PID))" "success"
    else
        print_status "Jorge Command Center: STOPPED" "error"
    fi

    echo
    print_status "Demo URLs:" "info"
    echo "   🔗 API Documentation: http://localhost:$FASTAPI_PORT/docs"
    echo "   🔗 Main Dashboard: http://localhost:$STREAMLIT_MAIN_PORT"
    echo "   🔗 Jorge Command Center: http://localhost:$STREAMLIT_JORGE_PORT"
}

start_all_services() {
    print_header

    check_dependencies
    check_ports

    print_status "Starting all demo services..." "info"
    echo

    start_fastapi
    start_streamlit_main
    start_streamlit_jorge

    echo
    print_status "All services started! Waiting for full initialization..." "info"
    sleep 10

    # Validate services are responding
    if curl -s http://localhost:$FASTAPI_PORT/docs > /dev/null; then
        print_status "FastAPI responding correctly" "success"
    else
        print_status "FastAPI not responding - check logs" "error"
    fi

    if curl -s http://localhost:$STREAMLIT_MAIN_PORT > /dev/null; then
        print_status "Main Dashboard responding correctly" "success"
    else
        print_status "Main Dashboard not responding - check logs" "error"
    fi

    if curl -s http://localhost:$STREAMLIT_JORGE_PORT > /dev/null; then
        print_status "Jorge Command Center responding correctly" "success"
    else
        print_status "Jorge Command Center not responding - check logs" "error"
    fi

    echo
    print_status "🎉 Demo environment ready for client presentation!" "success"
    echo
    print_status "Demo URLs:" "info"
    echo "   🔗 API Documentation: http://localhost:$FASTAPI_PORT/docs"
    echo "   🔗 Main Dashboard: http://localhost:$STREAMLIT_MAIN_PORT"
    echo "   🔗 Jorge Command Center: http://localhost:$STREAMLIT_JORGE_PORT"
    echo
    print_status "Next steps:" "info"
    echo "   1. Run: python3 setup_demo_environment.py"
    echo "   2. Open CLIENT_DEMO_SCENARIOS.md for demo scripts"
    echo "   3. Review CLIENT_PRESENTATION_DECK.md for talking points"
    echo
    print_status "Good luck with your demonstration! 🚀" "success"
}

# Main execution
case "${1:-start}" in
    "start")
        start_all_services
        ;;
    "stop")
        print_header
        stop_all_services
        ;;
    "restart")
        print_header
        stop_all_services
        sleep 2
        start_all_services
        ;;
    "status")
        print_header
        show_service_status
        ;;
    *)
        echo "Usage: $0 [start|stop|restart|status]"
        echo
        echo "Commands:"
        echo "  start   - Start all demo services (default)"
        echo "  stop    - Stop all demo services"
        echo "  restart - Stop and restart all services"
        echo "  status  - Show current service status"
        exit 1
        ;;
esac