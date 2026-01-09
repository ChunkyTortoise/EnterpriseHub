#!/usr/bin/env python3
"""
Enhanced Lead Intelligence System - ML Dependencies Validation
Validates that all required ML packages are properly installed and functional.
"""

import sys
import importlib
from typing import List, Tuple

def validate_package(module_name: str, display_name: str) -> Tuple[bool, str]:
    """Validate that a package can be imported and get its version."""
    try:
        module = importlib.import_module(module_name)
        version = getattr(module, '__version__', 'unknown')
        return True, version
    except ImportError as e:
        return False, str(e)
    except Exception as e:
        return False, f"Error: {str(e)}"

def test_functionality() -> bool:
    """Test core ML functionality."""
    try:
        # Test XGBoost + SHAP integration
        import xgboost as xgb
        import shap
        import numpy as np
        
        # Create sample data
        X = np.random.randn(50, 5)
        y = np.random.randint(0, 2, 50)
        
        # Train XGBoost model
        dtrain = xgb.DMatrix(X, label=y)
        params = {'objective': 'binary:logistic', 'eval_metric': 'logloss', 'verbosity': 0}
        model = xgb.train(params, dtrain, num_boost_round=5)
        
        # Test SHAP explainer
        explainer = shap.TreeExplainer(model)
        X_test = np.random.randn(10, 5)
        shap_values = explainer.shap_values(X_test)
        
        return True
    except Exception as e:
        print(f"❌ Functionality test failed: {e}")
        return False

def main():
    """Main validation function."""
    print("🔍 Enhanced Lead Intelligence System - ML Dependencies Validation")
    print("=" * 70)
    print(f"🐍 Python {sys.version.split()[0]} on {sys.platform}")
    print()
    
    # Define packages to validate
    packages = [
        ('redis', 'Redis'),
        ('xgboost', 'XGBoost'),
        ('shap', 'SHAP'),
        ('sklearn', 'Scikit-learn'),
        ('numpy', 'NumPy'),
        ('pandas', 'Pandas'),
        ('scipy', 'SciPy'),
        ('matplotlib', 'Matplotlib'),
        ('seaborn', 'Seaborn'),
        ('imblearn', 'Imbalanced-learn'),
        ('category_encoders', 'Category Encoders'),
        ('statsmodels', 'Statsmodels'),
        ('numba', 'Numba'),
        ('joblib', 'Joblib'),
    ]
    
    # Validate all packages
    successful = []
    failed = []
    
    for module_name, display_name in packages:
        success, version = validate_package(module_name, display_name)
        if success:
            print(f"✅ {display_name}: {version}")
            successful.append(display_name)
        else:
            print(f"❌ {display_name}: {version}")
            failed.append(display_name)
    
    print()
    print("=" * 70)
    
    # Test core functionality
    print("🧪 Testing ML Pipeline Functionality...")
    functionality_test = test_functionality()
    
    if functionality_test:
        print("✅ ML functionality test passed")
    
    # Summary
    print()
    print("📊 Validation Summary:")
    print(f"✅ Successfully validated: {len(successful)}/{len(packages)} packages")
    
    if failed:
        print(f"❌ Failed validations: {failed}")
        print("\n🔧 To install missing packages, run:")
        print("pip install " + " ".join([f'"{pkg.lower().replace(" ", "-").replace("scikit-learn", "scikit-learn")}"' 
                                       for pkg in failed]))
    
    # Overall status
    all_core_working = all(pkg in successful for pkg in ['Redis', 'XGBoost', 'SHAP', 'Scikit-learn'])
    
    if all_core_working and functionality_test:
        print("\n🎉 Enhanced Lead Intelligence System is ready!")
        print("🚀 All core ML dependencies are properly installed and functional.")
        return True
    else:
        print("\n⚠️  Some issues detected. Please resolve before proceeding.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
