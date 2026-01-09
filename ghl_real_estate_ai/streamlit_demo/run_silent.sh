#!/bin/bash
export PYTHONWARNINGS="ignore"
export STREAMLIT_CLIENT_SHOW_ERROR_DETAILS=false
python3 -m streamlit run app.py --server.port 8502 --client.showErrorDetails=false --server.headless=true
