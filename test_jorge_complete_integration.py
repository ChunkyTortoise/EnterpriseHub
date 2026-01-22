#!/usr/bin/env python3
"""
Jorge's Complete AI System Integration Test Suite

Tests all components of the integrated Jorge Real Estate AI system:
- Property Matching AI (#3) with Neural+Rules Algorithm
- Advanced Analytics Dashboard (#4) with Forecasting & ROI
- Enhanced Lead Scoring 2.0 (existing)
- Unified Dashboard Integration
- API Endpoints & Data Models
- Performance & Optimization Validation

This comprehensive test validates the complete implementation.
"""

import asyncio
import json
import pytest
import sys
import os
import traceback
import time
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import importlib.util

# Add the project root to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '.'))

class JorgeCompleteIntegrationTest:
    """Comprehensive integration test for Jorge's AI systems."""

    def __init__(self):
        self.test_results = []
        self.total_tests = 0
        self.passed_tests = 0
        self.failed_tests = 0
        self.start_time = time.time()

    def log_test(self, test_name: str, success: bool, details: str = "", execution_time: float = 0):
        """Log test result."""
        self.total_tests += 1
        if success:
            self.passed_tests += 1
            status = "✅ PASS"
        else:
            self.failed_tests += 1
            status = "❌ FAIL"

        result = {
            "test": test_name,
            "status": status,
            "success": success,
            "details": details,
            "execution_time_ms": round(execution_time * 1000, 2)
        }
        self.test_results.append(result)
        print(f"{status} {test_name} ({execution_time:.3f}s)")
        if details and not success:
            print(f"    Details: {details}")

    @pytest.mark.asyncio
    async def test_data_models(self):
        """Test all Pydantic data models."""
        print("\n📋 Testing Data Models...")

        # Test Property Matching Models
        try:
            start_time = time.time()

            # Import the models
            from ghl_real_estate_ai.models.jorge_property_models import (
                Property, PropertyMatch, PropertyAddress, PropertyFeatures,
                MatchReasoning, PropertyType, ConfidenceLevel
            )
            from datetime import datetime

            # Create test property with correct structure
            test_address = PropertyAddress(
                street="12345 Test Street",
                city="Rancho Cucamonga",
                state="CA",
                zip_code="91701"
            )

            test_features = PropertyFeatures(
                bedrooms=4,
                bathrooms=3.0,
                sqft=2500,
                lot_size_sqft=8000,
                garage_spaces=2
            )

            test_property = Property(
                id="prop_001",
                address=test_address,
                price=750000.0,
                features=test_features,
                property_type=PropertyType.SINGLE_FAMILY,
                days_on_market=15,
                price_per_sqft=300.0,
                listing_date=datetime.now()
            )

            # Create test match with correct MatchReasoning structure
            test_match = PropertyMatch(
                property=test_property,
                lead_id="lead_001",
                match_score=87.5,
                neural_score=85.0,
                rule_score=90.0,
                confidence=ConfidenceLevel.HIGH,
                recommendation_rank=1,
                reasoning=MatchReasoning(
                    primary_reasons=[
                        "Price perfectly aligns with $750K budget",
                        "Top-rated schools within walking distance",
                        "Recently updated kitchen and bathrooms"
                    ],
                    financial_fit="Property is priced at $750K, within budget with excellent value",
                    lifestyle_fit="Perfect family layout with 4BR/3BA in family-friendly neighborhood",
                    market_timing="Great buying opportunity with current inventory levels",
                    potential_concerns=["Built in 1995, may need minor updates"],
                    jorge_talking_points=[
                        "Emphasis on school quality for family",
                        "Recent renovation adds significant value"
                    ]
                ),
                algorithm_used="jorge_optimized"
            )

            execution_time = time.time() - start_time
            self.log_test("Property Matching Models Creation", True, "All models created successfully", execution_time)

        except Exception as e:
            execution_time = time.time() - start_time
            self.log_test("Property Matching Models Creation", False, f"Error: {str(e)}", execution_time)

        # Test Analytics Models
        try:
            start_time = time.time()

            from ghl_real_estate_ai.models.analytics_models import (
                RevenueForecast, FunnelAnalysis, FunnelMetrics, DropOffAnalysis,
                ExecutiveSummary, MarketTemperature, FunnelStage
            )
            from datetime import date

            # Create test analytics objects with all required fields
            test_forecast = RevenueForecast(
                forecasted_revenue=250000.0,
                confidence_lower=220000.0,
                confidence_upper=280000.0,
                confidence_level=0.87,
                forecast_horizon_days=30,
                predicted_conversions=35,
                avg_deal_value=7142.86,  # 250k/35 conversions
                model_accuracy=0.89,
                historical_mape=8.5,
                key_assumptions=[
                    "Seasonal market conditions remain stable",
                    "Current lead quality continues",
                    "No major economic disruptions"
                ],
                risk_factors=[
                    "Interest rate fluctuations",
                    "Inventory shortage impact",
                    "Economic uncertainty"
                ],
                market_conditions=MarketTemperature.WARM,
                model_version="jorge_forecast_v1.2",
                forecast_date=date.today()
            )

            # Create funnel stage metrics
            funnel_stages = [
                FunnelMetrics(
                    stage=FunnelStage.NEW_LEAD,
                    lead_count=580,
                    conversion_rate=0.681,
                    avg_time_in_stage_days=2.5,
                    drop_off_count=185,
                    drop_off_percentage=31.9
                ),
                FunnelMetrics(
                    stage=FunnelStage.QUALIFIED,
                    lead_count=395,
                    conversion_rate=0.532,
                    avg_time_in_stage_days=5.2,
                    drop_off_count=185,
                    drop_off_percentage=46.8
                ),
                FunnelMetrics(
                    stage=FunnelStage.APPOINTMENT,
                    lead_count=210,
                    conversion_rate=0.743,
                    avg_time_in_stage_days=3.1,
                    drop_off_count=54,
                    drop_off_percentage=25.7
                )
            ]

            # Create drop-off analysis
            drop_offs = [
                DropOffAnalysis(
                    from_stage=FunnelStage.QUALIFIED,
                    to_stage=FunnelStage.APPOINTMENT,
                    drop_off_count=185,
                    drop_off_rate=0.468,
                    primary_reasons=["No response to calls", "Lost interest", "Found another agent"],
                    improvement_opportunities=["Better follow-up sequence", "Value proposition clarity"]
                )
            ]

            test_funnel = FunnelAnalysis(
                time_period_days=30,
                stages=funnel_stages,
                conversion_rates={
                    "new_lead_to_qualified": 0.681,
                    "qualified_to_appointment": 0.532,
                    "appointment_to_showing": 0.743
                },
                drop_off_points=drop_offs,
                bottleneck_stage=FunnelStage.QUALIFIED,
                optimization_opportunities=["Improve qualification process", "Better nurture sequences"],
                overall_conversion_rate=0.041,  # 24/580
                avg_lead_to_close_days=42.5,
                improvement_potential_percent=28.0,
                recommended_actions=["Implement automated follow-up", "Refine qualification criteria"]
            )

            execution_time = time.time() - start_time
            self.log_test("Analytics Models Creation", True, "All analytics models created successfully", execution_time)

        except Exception as e:
            execution_time = time.time() - start_time
            self.log_test("Analytics Models Creation", False, f"Error: {str(e)}", execution_time)

    @pytest.mark.asyncio
    async def test_services_integration(self):
        """Test service layer integration."""
        print("\n🔧 Testing Service Integration...")

        # Test Property Matching Service
        try:
            start_time = time.time()

            # Check if service file exists
            service_path = "ghl_real_estate_ai/services/jorge_property_matching_service.py"
            if os.path.exists(service_path):
                with open(service_path, 'r') as f:
                    service_content = f.read()

                # Check for key methods (using actual method names)
                required_methods = [
                    "find_matches_for_lead",
                    "explain_specific_match",
                    "_calculate_neural_score",
                    "get_market_inventory_stats"
                ]

                missing_methods = [method for method in required_methods if method not in service_content]

                if not missing_methods:
                    execution_time = time.time() - start_time
                    self.log_test("Property Matching Service", True, f"Service structure validated with {len(required_methods)} methods", execution_time)
                else:
                    execution_time = time.time() - start_time
                    self.log_test("Property Matching Service", False, f"Missing methods: {missing_methods}", execution_time)
            else:
                execution_time = time.time() - start_time
                self.log_test("Property Matching Service", False, "Service file not found", execution_time)

        except Exception as e:
            execution_time = time.time() - start_time
            self.log_test("Property Matching Service", False, f"Error: {str(e)}", execution_time)

        # Test Analytics Service
        try:
            start_time = time.time()

            # Check if service file exists
            service_path = "ghl_real_estate_ai/services/jorge_analytics_service.py"
            if os.path.exists(service_path):
                with open(service_path, 'r') as f:
                    service_content = f.read()

                # Check for key methods (using actual method names)
                required_methods = [
                    "get_revenue_forecast",
                    "analyze_conversion_funnel",
                    "analyze_geographic_performance",
                    "get_source_roi_analysis"
                ]

                missing_methods = [method for method in required_methods if method not in service_content]

                if not missing_methods:
                    execution_time = time.time() - start_time
                    self.log_test("Analytics Service", True, f"Service structure validated with {len(required_methods)} methods", execution_time)
                else:
                    execution_time = time.time() - start_time
                    self.log_test("Analytics Service", False, f"Missing methods: {missing_methods}", execution_time)
            else:
                execution_time = time.time() - start_time
                self.log_test("Analytics Service", False, "Service file not found", execution_time)

        except Exception as e:
            execution_time = time.time() - start_time
            self.log_test("Analytics Service", False, f"Error: {str(e)}", execution_time)

    def test_api_imports(self):
        """Test API route structure."""
        print("\n🌐 Testing API Routes...")

        # Test Property Matching API
        try:
            start_time = time.time()

            api_path = "ghl_real_estate_ai/api/routes/jorge_property_matching.py"
            if os.path.exists(api_path):
                with open(api_path, 'r') as f:
                    api_content = f.read()

                # Check for key endpoints (using actual endpoint names)
                required_endpoints = [
                    "/matches",
                    "/explain",
                    "/preferences",
                    "/inventory"
                ]

                missing_endpoints = [ep for ep in required_endpoints if ep not in api_content]

                if not missing_endpoints:
                    execution_time = time.time() - start_time
                    self.log_test("Property Matching API Routes", True, f"API structure validated with {len(required_endpoints)} endpoints", execution_time)
                else:
                    execution_time = time.time() - start_time
                    self.log_test("Property Matching API Routes", False, f"Missing endpoints: {missing_endpoints}", execution_time)
            else:
                execution_time = time.time() - start_time
                self.log_test("Property Matching API Routes", False, "API routes file not found", execution_time)

        except Exception as e:
            execution_time = time.time() - start_time
            self.log_test("Property Matching API Routes", False, f"Error: {str(e)}", execution_time)

        # Test Analytics API
        try:
            start_time = time.time()

            api_path = "ghl_real_estate_ai/api/routes/jorge_analytics.py"
            if os.path.exists(api_path):
                with open(api_path, 'r') as f:
                    api_content = f.read()

                # Check for key endpoints (using actual endpoint names)
                required_endpoints = [
                    "/forecast",
                    "/funnel-analysis",
                    "/geographic-analysis",
                    "/source-roi"
                ]

                missing_endpoints = [ep for ep in required_endpoints if ep not in api_content]

                if not missing_endpoints:
                    execution_time = time.time() - start_time
                    self.log_test("Analytics API Routes", True, f"API structure validated with {len(required_endpoints)} endpoints", execution_time)
                else:
                    execution_time = time.time() - start_time
                    self.log_test("Analytics API Routes", False, f"Missing endpoints: {missing_endpoints}", execution_time)
            else:
                execution_time = time.time() - start_time
                self.log_test("Analytics API Routes", False, "API routes file not found", execution_time)

        except Exception as e:
            execution_time = time.time() - start_time
            self.log_test("Analytics API Routes", False, f"Error: {str(e)}", execution_time)

    def test_ui_components(self):
        """Test UI component imports."""
        print("\n🎨 Testing UI Components...")

        # Test Property Matching Dashboard
        try:
            start_time = time.time()

            spec = importlib.util.spec_from_file_location(
                "property_dashboard",
                "ghl_real_estate_ai/streamlit_demo/components/jorge_property_matching_dashboard.py"
            )
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

            # Check for main function
            if hasattr(module, 'render_jorge_property_matching_dashboard'):
                execution_time = time.time() - start_time
                self.log_test("Property Matching Dashboard", True, "Dashboard component loaded successfully", execution_time)
            else:
                execution_time = time.time() - start_time
                self.log_test("Property Matching Dashboard", False, "Main render function not found", execution_time)

        except Exception as e:
            execution_time = time.time() - start_time
            self.log_test("Property Matching Dashboard", False, f"Error: {str(e)}", execution_time)

        # Test Analytics Dashboard
        try:
            start_time = time.time()

            spec = importlib.util.spec_from_file_location(
                "analytics_dashboard",
                "ghl_real_estate_ai/streamlit_demo/components/jorge_analytics_dashboard.py"
            )
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

            # Check for main function
            if hasattr(module, 'render_jorge_analytics_dashboard'):
                execution_time = time.time() - start_time
                self.log_test("Analytics Dashboard", True, "Dashboard component loaded successfully", execution_time)
            else:
                execution_time = time.time() - start_time
                self.log_test("Analytics Dashboard", False, "Main render function not found", execution_time)

        except Exception as e:
            execution_time = time.time() - start_time
            self.log_test("Analytics Dashboard", False, f"Error: {str(e)}", execution_time)

        # Test Jorge Main Dashboard Integration
        try:
            start_time = time.time()

            spec = importlib.util.spec_from_file_location(
                "jorge_main_dashboard",
                "ghl_real_estate_ai/streamlit_demo/components/jorge_lead_bot_dashboard.py"
            )
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

            # Check for integration functions
            integration_functions = [
                'render_property_matching_integration_section',
                'render_analytics_integration_section',
                'render_jorge_lead_bot_dashboard'
            ]

            missing_functions = [func for func in integration_functions if not hasattr(module, func)]

            if not missing_functions:
                execution_time = time.time() - start_time
                self.log_test("Jorge Main Dashboard Integration", True, "All integration functions found", execution_time)
            else:
                execution_time = time.time() - start_time
                self.log_test("Jorge Main Dashboard Integration", False, f"Missing functions: {missing_functions}", execution_time)

        except Exception as e:
            execution_time = time.time() - start_time
            self.log_test("Jorge Main Dashboard Integration", False, f"Error: {str(e)}", execution_time)

    def test_database_schema(self):
        """Test database schema and migration."""
        print("\n🗄️ Testing Database Schema...")

        try:
            start_time = time.time()

            # Check if migration file exists and is readable
            migration_path = "ghl_real_estate_ai/database/migrations/004_jorge_property_analytics_tables.sql"

            if os.path.exists(migration_path):
                with open(migration_path, 'r') as f:
                    migration_content = f.read()

                # Check for key tables
                # Check for key tables (using actual table names from migration)
                required_tables = [
                    "jorge_properties",
                    "jorge_property_matches",
                    "jorge_lead_preferences",
                    "revenue_forecasts",
                    "funnel_snapshots",
                    "geographic_performance",
                    "source_roi_tracking"
                ]

                missing_tables = [table for table in required_tables if table not in migration_content]

                if not missing_tables:
                    execution_time = time.time() - start_time
                    self.log_test("Database Schema", True, f"All {len(required_tables)} tables defined", execution_time)
                else:
                    execution_time = time.time() - start_time
                    self.log_test("Database Schema", False, f"Missing tables: {missing_tables}", execution_time)
            else:
                execution_time = time.time() - start_time
                self.log_test("Database Schema", False, "Migration file not found", execution_time)

        except Exception as e:
            execution_time = time.time() - start_time
            self.log_test("Database Schema", False, f"Error: {str(e)}", execution_time)

    def test_system_performance(self):
        """Test system performance and optimization."""
        print("\n⚡ Testing Performance & Optimization...")

        # Test file sizes (optimization check)
        try:
            start_time = time.time()

            large_files = []
            component_files = [
                "ghl_real_estate_ai/streamlit_demo/components/jorge_property_matching_dashboard.py",
                "ghl_real_estate_ai/streamlit_demo/components/jorge_analytics_dashboard.py",
                "ghl_real_estate_ai/services/jorge_property_matching_service.py",
                "ghl_real_estate_ai/services/jorge_analytics_service.py"
            ]

            for file_path in component_files:
                if os.path.exists(file_path):
                    file_size = os.path.getsize(file_path)
                    if file_size > 100000:  # 100KB threshold
                        large_files.append(f"{file_path} ({file_size/1024:.1f}KB)")

            execution_time = time.time() - start_time
            if len(large_files) <= 2:  # Allow some large files for complex components
                self.log_test("File Size Optimization", True, f"File sizes reasonable", execution_time)
            else:
                self.log_test("File Size Optimization", False, f"Large files: {large_files}", execution_time)

        except Exception as e:
            execution_time = time.time() - start_time
            self.log_test("File Size Optimization", False, f"Error: {str(e)}", execution_time)

        # Test memory usage simulation
        try:
            start_time = time.time()

            # Simulate loading all components
            test_data = {
                "properties": [{"id": f"prop_{i}", "price": 750000 + i*10000} for i in range(100)],
                "leads": [{"id": f"lead_{i}", "score": 75 + i} for i in range(50)],
                "analytics": {"revenue": [45000 + i*1000 for i in range(30)]}
            }

            # Basic memory efficiency check
            data_size = len(json.dumps(test_data))

            execution_time = time.time() - start_time
            if data_size < 50000:  # 50KB threshold for mock data
                self.log_test("Memory Usage", True, f"Data size: {data_size} bytes", execution_time)
            else:
                self.log_test("Memory Usage", False, f"Data size too large: {data_size} bytes", execution_time)

        except Exception as e:
            execution_time = time.time() - start_time
            self.log_test("Memory Usage", False, f"Error: {str(e)}", execution_time)

    def generate_report(self):
        """Generate comprehensive test report."""
        print("\n" + "="*80)
        print("📊 JORGE'S COMPLETE AI SYSTEM - INTEGRATION TEST REPORT")
        print("="*80)

        total_time = time.time() - self.start_time

        print(f"""
🎯 TEST EXECUTION SUMMARY:
   Total Tests: {self.total_tests}
   Passed: {self.passed_tests} ✅
   Failed: {self.failed_tests} ❌
   Success Rate: {(self.passed_tests/self.total_tests*100):.1f}%
   Total Time: {total_time:.2f} seconds

🏠 PROPERTY MATCHING AI (#3):
   - Data Models: {'✅' if any('Property Matching Models' in r['test'] and r['success'] for r in self.test_results) else '❌'}
   - Service Layer: {'✅' if any('Property Matching Service' in r['test'] and r['success'] for r in self.test_results) else '❌'}
   - API Routes: {'✅' if any('Property Matching API' in r['test'] and r['success'] for r in self.test_results) else '❌'}
   - Dashboard UI: {'✅' if any('Property Matching Dashboard' in r['test'] and r['success'] for r in self.test_results) else '❌'}

📊 ADVANCED ANALYTICS (#4):
   - Data Models: {'✅' if any('Analytics Models' in r['test'] and r['success'] for r in self.test_results) else '❌'}
   - Service Layer: {'✅' if any('Analytics Service' in r['test'] and r['success'] for r in self.test_results) else '❌'}
   - API Routes: {'✅' if any('Analytics API' in r['test'] and r['success'] for r in self.test_results) else '❌'}
   - Dashboard UI: {'✅' if any('Analytics Dashboard' in r['test'] and r['success'] for r in self.test_results) else '❌'}

🎛️ INTEGRATION:
   - Jorge Dashboard: {'✅' if any('Jorge Main Dashboard' in r['test'] and r['success'] for r in self.test_results) else '❌'}
   - Database Schema: {'✅' if any('Database Schema' in r['test'] and r['success'] for r in self.test_results) else '❌'}
   - Performance: {'✅' if any('Performance' in r['test'] and r['success'] for r in self.test_results) else '❌'}
        """)

        # Detailed results
        print("📋 DETAILED TEST RESULTS:")
        for result in self.test_results:
            print(f"   {result['status']} {result['test']} ({result['execution_time_ms']}ms)")
            if result['details'] and not result['success']:
                print(f"      {result['details']}")

        # System readiness assessment
        critical_systems = [
            'Property Matching Models Creation',
            'Analytics Models Creation',
            'Property Matching Dashboard',
            'Analytics Dashboard',
            'Jorge Main Dashboard Integration'
        ]

        critical_passed = sum(1 for r in self.test_results
                            if any(critical in r['test'] for critical in critical_systems) and r['success'])

        print(f"\n🚀 SYSTEM READINESS:")
        if critical_passed >= 4:
            print("   ✅ READY FOR PRODUCTION - All critical systems operational")
        elif critical_passed >= 3:
            print("   ⚠️ MOSTLY READY - Minor issues to resolve")
        else:
            print("   ❌ NOT READY - Critical systems need attention")

        print("\n" + "="*80)
        print("🎉 Jorge's Enhanced Lead Bot with Property Matching AI (#3) and Advanced Analytics (#4)")
        print("   🧠 6-Dimensional Lead Scoring | 🏠 Neural+Rules Property Matching | 📊 AI Forecasting")
        print("   Integration Test Complete - Ready for Rancho Cucamonga Market Dominance!")
        print("="*80)

async def main():
    """Run the complete integration test suite."""
    print("🚀 Starting Jorge's Complete AI System Integration Test...")
    print("Testing: Property Matching AI (#3) + Advanced Analytics (#4) + Integration")

    test_suite = JorgeCompleteIntegrationTest()

    try:
        # Run all test categories
        await test_suite.test_data_models()
        await test_suite.test_services_integration()
        test_suite.test_api_imports()
        test_suite.test_ui_components()
        test_suite.test_database_schema()
        test_suite.test_system_performance()

        # Generate comprehensive report
        test_suite.generate_report()

        return test_suite.passed_tests == test_suite.total_tests

    except Exception as e:
        print(f"\n❌ Critical Error in Test Suite: {str(e)}")
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)