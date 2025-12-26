#!/bin/bash
# Setup script for automated screenshot capture

echo "================================================"
echo "EnterpriseHub Screenshot Automation Setup"
echo "================================================"

# Check Python version
echo ""
echo "Checking Python version..."
python3 --version

# Install Playwright and Pillow
echo ""
echo "Installing dependencies..."
pip install playwright pillow

# Install Chromium browser for Playwright
echo ""
echo "Installing Chromium browser..."
playwright install chromium

echo ""
echo "================================================"
echo "✅ Setup complete!"
echo "================================================"
echo ""
echo "To capture screenshots, run:"
echo "   cd assets"
echo "   python3 auto_screenshot.py"
echo ""
echo "The script will:"
echo "  - Open your live demo automatically"
echo "  - Navigate through all modules"
echo "  - Capture 12 screenshots (3 require manual upload)"
echo "  - Save to /assets/screenshots/"
echo "  - Optimize file sizes"
echo ""
echo "Estimated time: 5-10 minutes"
