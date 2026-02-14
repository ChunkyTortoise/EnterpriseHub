#!/bin/bash
# GHL Real Estate AI - Demo Setup Script
# Automated setup for demonstration environment

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Welcome message
echo "=================================================="
echo "🚀 GHL Real Estate AI - Demo Setup"
echo "=================================================="
echo ""
print_status "Setting up your AI-powered real estate platform..."
echo ""

# Check Python version
print_status "Checking Python version..."
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
    print_success "Python $PYTHON_VERSION found"
else
    print_error "Python 3.11+ is required but not found"
    exit 1
fi

# Check if we're in the right directory
if [[ ! -f "requirements.txt" ]]; then
    print_error "requirements.txt not found. Please run this script from the project root directory."
    exit 1
fi

# Create virtual environment
print_status "Creating virtual environment..."
if [[ ! -d "venv" ]]; then
    python3 -m venv venv
    print_success "Virtual environment created"
else
    print_warning "Virtual environment already exists"
fi

# Activate virtual environment
print_status "Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
print_status "Upgrading pip..."
pip install --upgrade pip > /dev/null 2>&1

# Install dependencies
print_status "Installing dependencies (this may take a few minutes)..."
pip install -r requirements.txt > /dev/null 2>&1
print_success "All dependencies installed successfully"

# Create data directories
print_status "Creating data directories..."
mkdir -p data/memory
mkdir -p data/workflows  
mkdir -p data/telemetry
mkdir -p data/marketplace
mkdir -p data/tenants
mkdir -p logs
print_success "Data directories created"

# Setup environment file
if [[ ! -f ".env" ]]; then
    print_status "Setting up environment configuration..."
    cp .env.example .env
    print_warning "Please edit .env file with your API keys:"
    echo "  1. Get Claude API key from: https://console.anthropic.com/"
    echo "  2. Get GHL API key from your GoHighLevel settings"
    echo "  3. Update ANTHROPIC_API_KEY and GHL_API_KEY in .env"
    echo ""
    print_warning "The demo will work with demo data even without API keys for testing"
else
    print_success "Environment file already exists"
fi

# Create demo data if needed
print_status "Setting up demo data..."
python3 << 'PYTHON'
import json
import os
from datetime import datetime, timedelta
import random

# Create demo lead data
demo_leads = []
lead_names = [
    "Sarah Chen", "Michael Rodriguez", "Emily Johnson", "David Kim", 
    "Jessica Williams", "Robert Thompson", "Lisa Zhang", "James Wilson",
    "Maria Garcia", "Kevin Lee", "Amanda Davis", "Christopher Brown",
    "Nicole Martinez", "Steven Taylor", "Rachel Anderson", "Daniel White"
]

properties = [
    "Downtown Rancho Cucamonga Condo", "Lake Travis Mansion", "South Rancho Cucamonga Bungalow",
    "West Lake Hills Estate", "East Rancho Cucamonga Townhouse", "Cedar Park Family Home",
    "Barton Creek Luxury Villa", "Mueller Community Home", "Zilker Condo",
    "Round Rock Suburb House", "Georgetown Historic Home", "Dripping Springs Ranch"
]

for i, name in enumerate(lead_names):
    first, last = name.split()
    demo_lead = {
        "id": f"demo_{i+1}",
        "firstName": first,
        "lastName": last,
        "email": f"{first.lower()}.{last.lower()}@example.com",
        "phone": f"512-555-{1000 + i:04d}",
        "score": random.randint(25, 95),
        "status": random.choice(["new", "qualified", "nurture", "hot"]),
        "budget": random.choice([300000, 450000, 600000, 750000, 900000, 1200000]),
        "preferences": {
            "bedrooms": random.choice([2, 3, 4, 5]),
            "location": random.choice(["Downtown", "West Lake Hills", "South Rancho Cucamonga", "Cedar Park"]),
            "property_type": random.choice(["Condo", "House", "Townhouse", "Estate"])
        },
        "activity": {
            "last_contact": (datetime.now() - timedelta(days=random.randint(1, 30))).isoformat(),
            "portal_visits": random.randint(2, 25),
            "properties_viewed": random.randint(5, 50),
            "engagement_score": random.randint(30, 100)
        },
        "interested_property": random.choice(properties)
    }
    demo_leads.append(demo_lead)

# Save demo data
os.makedirs("data/demo", exist_ok=True)
with open("data/demo/leads.json", "w") as f:
    json.dump(demo_leads, f, indent=2)

# Create demo pipeline data
pipeline_data = {
    "total_value": 2400000,
    "active_deals": 12,
    "conversion_rate": 24.5,
    "avg_deal_size": 200000,
    "monthly_revenue": 180000,
    "leads_this_month": 87,
    "deals_closed": 8
}

with open("data/demo/pipeline.json", "w") as f:
    json.dump(pipeline_data, f, indent=2)

print("Demo data created successfully")
PYTHON

print_success "Demo data setup complete"

# Test basic imports
print_status "Testing core imports..."
python3 << 'PYTHON'
try:
    import streamlit
    import pandas as pd
    import plotly.graph_objects as go
    import anthropic
    print("✅ All core dependencies available")
except ImportError as e:
    print(f"❌ Import error: {e}")
    exit(1)
PYTHON

# Final instructions
echo ""
echo "=================================================="
print_success "🎉 Demo setup completed successfully!"
echo "=================================================="
echo ""
echo "🚀 TO START THE DEMO:"
echo ""
echo "1. Update your API keys (if you have them):"
echo "   nano .env"
echo ""
echo "2. Start the demo:"
echo "   source venv/bin/activate"
echo "   cd ghl_real_estate_ai/streamlit_demo"
echo "   streamlit run app.py"
echo ""
echo "3. Open your browser to: http://localhost:8501"
echo ""
print_warning "Note: The demo works with sample data even without API keys"
print_status "For full functionality, add your Claude and GHL API keys to .env"
echo ""
echo "📖 Need help? Check GHL_TECHNICAL_DOCUMENTATION.md"
echo "=================================================="
