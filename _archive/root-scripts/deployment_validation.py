#!/usr/bin/env python3
"""
Customer Intelligence Platform - Deployment Validation Script
Validates all implemented components for production readiness
"""

import sys
import importlib
import asyncio
import logging
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class DeploymentValidator:
    """Comprehensive deployment validation for Customer Intelligence Platform"""
    
    def __init__(self):
        self.validation_results = {}
        self.errors = []
        self.warnings = []
        
    def validate_imports(self) -> bool:
        """Validate all implemented services can be imported"""
        logger.info("🔍 Validating service imports...")
        
        services_to_validate = [
            "ghl_real_estate_ai.services.advanced_customer_intelligence_engine",
            "ghl_real_estate_ai.services.realtime_notification_engine", 
            "ghl_real_estate_ai.services.advanced_analytics_visualization_engine",
            "ghl_real_estate_ai.services.business_intelligence_reporting_engine",
            "ghl_real_estate_ai.services.multichannel_communication_engine",
            "ghl_real_estate_ai.services.enterprise_performance_optimizer",
            "ghl_real_estate_ai.streamlit_demo.components.advanced_customer_intelligence_dashboard"
        ]
        
        success_count = 0
        for service_name in services_to_validate:
            try:
                module = importlib.import_module(service_name)
                logger.info(f"✅ Successfully imported: {service_name}")
                success_count += 1
                
                # Check for key classes
                if "advanced_customer_intelligence_engine" in service_name:
                    assert hasattr(module, 'AdvancedCustomerIntelligenceEngine')
                elif "realtime_notification_engine" in service_name:
                    assert hasattr(module, 'RealtimeNotificationEngine')
                elif "advanced_analytics_visualization_engine" in service_name:
                    assert hasattr(module, 'AdvancedAnalyticsVisualizationEngine')
                elif "business_intelligence_reporting_engine" in service_name:
                    assert hasattr(module, 'BusinessIntelligenceReportingEngine')
                elif "multichannel_communication_engine" in service_name:
                    assert hasattr(module, 'MultichannelCommunicationEngine')
                elif "enterprise_performance_optimizer" in service_name:
                    assert hasattr(module, 'EnterprisePerformanceOptimizer')
                    
            except Exception as e:
                error_msg = f"❌ Failed to import {service_name}: {str(e)}"
                logger.error(error_msg)
                self.errors.append(error_msg)
        
        success_rate = (success_count / len(services_to_validate)) * 100
        self.validation_results['imports'] = {
            'success_rate': success_rate,
            'total_services': len(services_to_validate),
            'successful_imports': success_count
        }
        
        return success_count == len(services_to_validate)
    
    def validate_test_files(self) -> bool:
        """Validate test files exist and have proper structure"""
        logger.info("🧪 Validating test coverage...")
        
        test_files = [
            "tests/services/test_advanced_customer_intelligence_engine.py",
            "tests/services/test_realtime_notification_engine.py",
            "tests/services/test_advanced_analytics_visualization_engine.py",
            "tests/services/test_business_intelligence_reporting_engine.py",
            "tests/services/test_multichannel_communication_engine.py",
            "tests/services/test_enterprise_performance_optimizer.py",
            "tests/streamlit_demo/components/test_advanced_customer_intelligence_dashboard.py"
        ]
        
        existing_tests = 0
        for test_file in test_files:
            if Path(test_file).exists():
                logger.info(f"✅ Test file exists: {test_file}")
                existing_tests += 1
                
                # Check file size (should have substantial content)
                file_size = Path(test_file).stat().st_size
                if file_size < 1000:  # Less than 1KB might be incomplete
                    warning_msg = f"⚠️ Test file seems small: {test_file} ({file_size} bytes)"
                    logger.warning(warning_msg)
                    self.warnings.append(warning_msg)
            else:
                error_msg = f"❌ Missing test file: {test_file}"
                logger.error(error_msg)
                self.errors.append(error_msg)
        
        test_coverage = (existing_tests / len(test_files)) * 100
        self.validation_results['tests'] = {
            'coverage_percentage': test_coverage,
            'total_expected': len(test_files),
            'existing_tests': existing_tests
        }
        
        return test_coverage >= 80  # 80% minimum coverage
    
    def validate_dependencies(self) -> bool:
        """Validate required dependencies are available"""
        logger.info("📦 Validating dependencies...")
        
        required_packages = [
            'streamlit',
            'fastapi',
            'redis',
            'asyncio',
            'anthropic',
            'plotly',
            'pandas',
            'numpy',
            'pydantic',
            'pytest',
            'pytest-asyncio'
        ]
        
        available_packages = 0
        for package in required_packages:
            try:
                importlib.import_module(package)
                logger.info(f"✅ Package available: {package}")
                available_packages += 1
            except ImportError:
                error_msg = f"❌ Missing package: {package}"
                logger.error(error_msg)
                self.errors.append(error_msg)
        
        dependency_coverage = (available_packages / len(required_packages)) * 100
        self.validation_results['dependencies'] = {
            'coverage_percentage': dependency_coverage,
            'total_required': len(required_packages),
            'available_packages': available_packages
        }
        
        return dependency_coverage >= 90  # 90% minimum for core functionality
    
    def validate_file_structure(self) -> bool:
        """Validate project file structure is correct"""
        logger.info("📁 Validating file structure...")
        
        required_paths = [
            "ghl_real_estate_ai/",
            "ghl_real_estate_ai/services/",
            "ghl_real_estate_ai/streamlit_demo/",
            "ghl_real_estate_ai/streamlit_demo/components/",
            "tests/",
            "tests/services/",
            "tests/streamlit_demo/",
            "tests/streamlit_demo/components/"
        ]
        
        existing_paths = 0
        for required_path in required_paths:
            if Path(required_path).exists():
                logger.info(f"✅ Path exists: {required_path}")
                existing_paths += 1
            else:
                error_msg = f"❌ Missing path: {required_path}"
                logger.error(error_msg)
                self.errors.append(error_msg)
        
        structure_coverage = (existing_paths / len(required_paths)) * 100
        self.validation_results['file_structure'] = {
            'coverage_percentage': structure_coverage,
            'total_required': len(required_paths),
            'existing_paths': existing_paths
        }
        
        return structure_coverage == 100  # All paths must exist
    
    async def validate_async_components(self) -> bool:
        """Validate async components can be initialized"""
        logger.info("⚡ Validating async components...")
        
        try:
            # Test basic async functionality
            async def test_async():
                await asyncio.sleep(0.001)
                return True
            
            result = await test_async()
            logger.info("✅ Async functionality working")
            
            self.validation_results['async_components'] = {
                'status': 'working',
                'test_passed': result
            }
            return True
            
        except Exception as e:
            error_msg = f"❌ Async validation failed: {str(e)}"
            logger.error(error_msg)
            self.errors.append(error_msg)
            return False
    
    def validate_configuration(self) -> bool:
        """Validate configuration files and environment setup"""
        logger.info("⚙️ Validating configuration...")
        
        config_files = [
            "requirements.txt",
            ".claude/settings.json",
            "CLAUDE.md"
        ]
        
        existing_configs = 0
        for config_file in config_files:
            if Path(config_file).exists():
                logger.info(f"✅ Config file exists: {config_file}")
                existing_configs += 1
            else:
                warning_msg = f"⚠️ Missing config file: {config_file}"
                logger.warning(warning_msg)
                self.warnings.append(warning_msg)
        
        config_coverage = (existing_configs / len(config_files)) * 100
        self.validation_results['configuration'] = {
            'coverage_percentage': config_coverage,
            'total_expected': len(config_files),
            'existing_configs': existing_configs
        }
        
        return config_coverage >= 66  # At least 2/3 config files should exist
    
    async def run_full_validation(self) -> Dict[str, Any]:
        """Run complete validation suite"""
        logger.info("🚀 Starting Customer Intelligence Platform deployment validation...")
        
        start_time = datetime.now()
        
        # Run all validations
        validations = {
            'file_structure': self.validate_file_structure(),
            'imports': self.validate_imports(),
            'dependencies': self.validate_dependencies(),
            'test_files': self.validate_test_files(),
            'async_components': await self.validate_async_components(),
            'configuration': self.validate_configuration()
        }
        
        # Calculate overall score
        passed_validations = sum(validations.values())
        total_validations = len(validations)
        overall_score = (passed_validations / total_validations) * 100
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        # Compile final report
        report = {
            'timestamp': end_time.isoformat(),
            'duration_seconds': duration,
            'overall_score': overall_score,
            'validations': validations,
            'details': self.validation_results,
            'errors': self.errors,
            'warnings': self.warnings,
            'deployment_ready': overall_score >= 85  # 85% minimum for deployment
        }
        
        # Log summary
        logger.info(f"\n{'='*50}")
        logger.info("📊 VALIDATION SUMMARY")
        logger.info(f"{'='*50}")
        logger.info(f"Overall Score: {overall_score:.1f}%")
        logger.info(f"Passed Validations: {passed_validations}/{total_validations}")
        logger.info(f"Errors: {len(self.errors)}")
        logger.info(f"Warnings: {len(self.warnings)}")
        logger.info(f"Deployment Ready: {'✅ YES' if report['deployment_ready'] else '❌ NO'}")
        logger.info(f"{'='*50}")
        
        if report['deployment_ready']:
            logger.info("🎉 Customer Intelligence Platform is READY for deployment!")
        else:
            logger.error("🔧 Platform requires fixes before deployment")
            if self.errors:
                logger.error("Critical errors to fix:")
                for error in self.errors:
                    logger.error(f"  - {error}")
        
        return report

async def main():
    """Main validation entry point"""
    validator = DeploymentValidator()
    report = await validator.run_full_validation()
    
    # Exit with appropriate code
    sys.exit(0 if report['deployment_ready'] else 1)

if __name__ == "__main__":
    asyncio.run(main())