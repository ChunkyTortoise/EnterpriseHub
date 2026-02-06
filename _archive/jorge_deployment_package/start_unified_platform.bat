@echo off
echo 🚀 Starting Jorge's Unified Enhanced AI Bot Platform
echo ================================================================

echo 🤖 Starting Seller Bot FastAPI (Port 8002)...
start "Seller Bot" uvicorn jorge_fastapi_seller_bot:app --host 0.0.0.0 --port 8002

echo 🎛️ Starting Command Center Dashboard (Port 8501)...
start "Command Center" streamlit run jorge_unified_command_center.py --server.port 8501

echo 📊 Starting Performance Monitor (Port 8503)...
start "Monitor" streamlit run jorge_unified_monitoring.py --server.port 8503

timeout /t 5

echo.
echo 🎉 Jorge's Unified Platform is Running!
echo ================================================================
echo 🤖 Seller Bot API:       http://localhost:8002
echo 🎛️ Command Center:       http://localhost:8501
echo 📊 Performance Monitor:   http://localhost:8503
echo ================================================================

pause
