#!/bin/bash

# Enhanced Lead Intelligence System - ML Dependencies Installation
# Date: 2026-01-09
# Compatible with Python 3.14

set -e  # Exit on any error

VENV_PATH="/Users/cave/enterprisehub/ghl_real_estate_ai/streamlit_demo/.venv"
PIP_CMD="$VENV_PATH/bin/python -m pip"

echo "🚀 Installing ML dependencies for Enhanced Lead Intelligence System"
echo "Python version: $($VENV_PATH/bin/python --version)"
echo "Virtual environment: $VENV_PATH"
echo ""

# Function to install and verify package
install_and_verify() {
    local package=$1
    local verify_import=$2
    
    echo "📦 Installing $package..."
    if $PIP_CMD install "$package"; then
        echo "✅ $package installed successfully"
        
        # Verify import
        if [ -n "$verify_import" ]; then
            if $VENV_PATH/bin/python -c "import $verify_import; print(f'✓ {verify_import} imported successfully')"; then
                echo "✅ $package verification passed"
            else
                echo "⚠️  $package installed but import failed"
            fi
        fi
    else
        echo "❌ Failed to install $package"
        return 1
    fi
    echo ""
}

# Upgrade pip first
echo "🔧 Upgrading pip..."
$PIP_CMD install --upgrade pip setuptools wheel
echo ""

# Priority 1: Core caching and data storage
echo "🎯 Priority 1: Core Infrastructure"
install_and_verify "redis>=5.0.0,<6.0.0" "redis"

# Priority 2: Essential ML packages
echo "🎯 Priority 2: Essential ML Packages"
install_and_verify "xgboost>=2.0.0,<3.0.0" "xgboost"

# Priority 3: Model explainability
echo "🎯 Priority 3: Model Explainability"
install_and_verify "shap>=0.44.0,<1.0.0" "shap"

# Priority 4: Enhanced data visualization
echo "🎯 Priority 4: Enhanced Visualization"
install_and_verify "matplotlib>=3.8.0,<4.0.0" "matplotlib"
install_and_verify "seaborn>=0.13.0,<1.0.0" "seaborn"

# Priority 5: Advanced ML utilities
echo "🎯 Priority 5: Advanced ML Utilities"
install_and_verify "imbalanced-learn>=0.11.0,<1.0.0" "imblearn"
install_and_verify "category-encoders>=2.6.0,<3.0.0" "category_encoders"

# Priority 6: Time series and forecasting (may have compatibility issues with Python 3.14)
echo "🎯 Priority 6: Time Series & Forecasting (Optional)"
if install_and_verify "statsmodels>=0.14.0,<1.0.0" "statsmodels"; then
    echo "✅ Statsmodels installed successfully"
else
    echo "⚠️  Statsmodels failed - will continue without it"
fi

# Prophet might have issues with Python 3.14, so we'll try but not fail on error
if $PIP_CMD install "prophet>=1.1.4,<2.0.0" 2>/dev/null; then
    echo "✅ Prophet installed successfully"
else
    echo "⚠️  Prophet installation failed (common with Python 3.14) - skipping"
fi

# Priority 7: Performance optimization
echo "🎯 Priority 7: Performance Optimization"
install_and_verify "joblib>=1.3.0,<2.0.0" "joblib"
install_and_verify "memory-profiler>=0.61.0,<1.0.0" "memory_profiler"

# Optional: Try numba (might have compatibility issues)
if $PIP_CMD install "numba>=0.58.0,<1.0.0" 2>/dev/null; then
    echo "✅ Numba installed successfully"
else
    echo "⚠️  Numba installation failed (common with Python 3.14) - skipping"
fi

echo "🎉 ML dependencies installation completed!"
echo ""
echo "📋 Installation Summary:"
$PIP_CMD list | grep -E "(redis|xgboost|shap|matplotlib|seaborn|imbalanced|category|statsmodels|prophet|joblib|memory-profiler|numba)" | sort
