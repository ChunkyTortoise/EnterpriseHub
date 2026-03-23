#!/bin/bash
# Launch script for Professional Certifications Showcase
#
# Usage:
#   ./certifications/launch_showcase.sh
#   ./certifications/launch_showcase.sh --port 8506

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Default port
PORT=8506

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --port)
            PORT="$2"
            shift 2
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

echo "=========================================="
echo "Professional Certifications Showcase"
echo "=========================================="
echo "Project: EnterpriseHub Portfolio"
echo "Port: $PORT"
echo "URL: http://localhost:$PORT"
echo "=========================================="

# Launch Streamlit
cd "$PROJECT_ROOT"
python -m streamlit run ghl_real_estate_ai/streamlit_demo/certifications_showcase.py \
    --server.port $PORT \
    --server.headless false \
    --browser.gatherUsageStats false

echo "Showcase stopped."
