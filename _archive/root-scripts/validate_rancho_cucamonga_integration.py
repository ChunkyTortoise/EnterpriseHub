#!/usr/bin/env python3
"""
Rancho Cucamonga Market Integration Validation

This script validates that Jorge bots have been successfully updated from
Rancho Cucamonga, CA to Rancho Cucamonga, CA market focus. Tests include:

1. Configuration validation
2. Market data verification
3. Price range accuracy
4. Regulatory compliance
5. Neighborhood mapping
6. Bot responses and context

Author: Claude Code Assistant
Created: 2026-01-25
Purpose: Validate Rancho Cucamonga market integration
"""

import sys
import json
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import traceback

# Add project root to path
project_root = Path(__file__).parent
sys.path.append(str(project_root))

# Test imports
try:
    from ghl_real_estate_ai.ghl_utils.jorge_config import market_manager, CURRENT_MARKET, MARKET_CONFIG
    from ghl_real_estate_ai.ghl_utils.jorge_rancho_config import (
        rancho_config,
        RANCHO_NEIGHBORHOODS,
        RANCHO_PRICE_RANGES,
        CALIFORNIA_COMPLIANCE
    )
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Make sure all configuration files are properly set up.")
    sys.exit(1)


class RanchoMarketValidator:
    """Validates Rancho Cucamonga market integration"""

    def __init__(self):
        self.test_results = []
        self.passed_tests = 0
        self.failed_tests = 0

    def run_all_validations(self) -> Dict:
        """Run comprehensive validation suite"""
        print("🏠 Jorge Rancho Cucamonga Market Integration Validation")
        print("=" * 60)

        # Run all validation tests
        self._test_market_configuration()
        self._test_price_ranges()
        self._test_neighborhood_mapping()
        self._test_california_compliance()
        self._test_market_context()
        self._test_file_transformations()

        # Generate summary
        return self._generate_validation_report()

    def _test_market_configuration(self):
        """Test basic market configuration"""
        print("📍 Testing Market Configuration...")

        # Test 1: Current market should be Rancho Cucamonga
        try:
            assert CURRENT_MARKET == "rancho_cucamonga", f"Expected 'rancho_cucamonga', got '{CURRENT_MARKET}'"
            self._log_test("Current Market Setting", True, "Market set to Rancho Cucamonga")
        except Exception as e:
            self._log_test("Current Market Setting", False, str(e))

        # Test 2: Market config should be loaded
        try:
            assert MARKET_CONFIG is not None, "Market configuration is None"
            self._log_test("Market Config Loaded", True, "Market configuration available")
        except Exception as e:
            self._log_test("Market Config Loaded", False, str(e))

        # Test 3: Rancho config should be accessible
        try:
            config = rancho_config.MARKET_CONFIG
            assert config.MARKET_NAME == "Rancho Cucamonga"
            assert config.STATE_CODE == "CA"
            assert config.COUNTY == "San Bernardino County"
            self._log_test("Rancho Config Details", True, "All market details correct")
        except Exception as e:
            self._log_test("Rancho Config Details", False, str(e))

    def _test_price_ranges(self):
        """Test California price ranges"""
        print("💰 Testing Price Ranges...")

        expected_ranges = {
            "entry_level": {"min": 500000, "max": 700000},
            "mid_market": {"min": 700000, "max": 1200000},
            "luxury": {"min": 1200000, "max": 3000000}
        }

        try:
            ranges = rancho_config.MARKET_CONFIG.PRICE_RANGES
            for tier, expected in expected_ranges.items():
                actual = ranges.get(tier, {})
                assert actual.get("min") >= expected["min"], f"{tier} min price too low"
                assert actual.get("max") >= expected["max"], f"{tier} max price too low"

            self._log_test("California Price Ranges", True, "All price ranges updated for CA market")
        except Exception as e:
            self._log_test("California Price Ranges", False, str(e))

    def _test_neighborhood_mapping(self):
        """Test neighborhood mapping from Rancho Cucamonga to Rancho Cucamonga"""
        print("🏘️ Testing Neighborhood Mapping...")

        expected_neighborhoods = [
            "alta_loma", "central_rc", "etiwanda",
            "victoria_gardens", "terra_vista", "day_creek"
        ]

        try:
            neighborhoods = rancho_config.MARKET_CONFIG.NEIGHBORHOODS
            for neighborhood in expected_neighborhoods:
                assert neighborhood in neighborhoods, f"Missing neighborhood: {neighborhood}"
                config = neighborhoods[neighborhood]
                assert "median_price" in config, f"Missing median_price for {neighborhood}"
                assert "characteristics" in config, f"Missing characteristics for {neighborhood}"
                assert config["median_price"] > 500000, f"Median price too low for CA market in {neighborhood}"

            self._log_test("Neighborhood Configuration", True, "All neighborhoods properly configured")
        except Exception as e:
            self._log_test("Neighborhood Configuration", False, str(e))

    def _test_california_compliance(self):
        """Test California regulatory compliance"""
        print("⚖️ Testing California Compliance...")

        try:
            compliance = rancho_config.MARKET_CONFIG.REGULATORY_FRAMEWORK

            # Test DRE (not TREC)
            assert compliance["license_authority"] == "DRE", "Should use DRE, not TREC"
            assert "California" in compliance["license_authority_full"], "Should reference California"
            assert "state_regulations" in compliance, "Missing state regulations"

            # Test California-specific disclosures
            disclosures = compliance.get("disclosure_requirements", [])
            ca_disclosures = [
                "Natural Hazard Disclosure Statement",
                "Earthquake Safety Disclosure",
                "Transfer Disclosure Statement"
            ]
            for disclosure in ca_disclosures:
                assert disclosure in disclosures, f"Missing CA disclosure: {disclosure}"

            self._log_test("California Compliance", True, "All compliance requirements correct")
        except Exception as e:
            self._log_test("California Compliance", False, str(e))

    def _test_market_context(self):
        """Test market context and intelligence"""
        print("🧠 Testing Market Intelligence...")

        try:
            market_data = rancho_config.MARKET_CONFIG.MARKET_CHARACTERISTICS

            # Test market drivers
            drivers = market_data.get("primary_drivers", [])
            ca_indicators = ["affordable", "family", "schools", "Ontario", "mountain"]
            ca_found = any(any(indicator.lower() in driver.lower() for indicator in ca_indicators) for driver in drivers)
            assert ca_found, "Market drivers should reflect CA/Rancho market"

            # Test buyer demographics
            demographics = market_data.get("buyer_demographics", [])
            assert len(demographics) > 0, "Missing buyer demographics"

            self._log_test("Market Intelligence", True, "Market context properly configured")
        except Exception as e:
            self._log_test("Market Intelligence", False, str(e))

    def _test_file_transformations(self):
        """Test that key files were transformed"""
        print("📁 Testing File Transformations...")

        key_files = [
            "ghl_real_estate_ai/agents/jorge_seller_bot.py",
            "ghl_real_estate_ai/agents/jorge_buyer_bot.py",
            "ghl_real_estate_ai/ghl_utils/jorge_config.py",
            "CLAUDE.md"
        ]

        for file_path in key_files:
            try:
                full_path = project_root / file_path
                if not full_path.exists():
                    self._log_test(f"File exists: {file_path}", False, "File not found")
                    continue

                with open(full_path, 'r', encoding='utf-8') as f:
                    content = f.read()

                # Check for Rancho Cucamonga references
                has_rancho = "rancho_cucamonga" in content.lower() or "rancho cucamonga" in content.lower()

                # Check for absence of Rancho Cucamonga references (with some exceptions)
                rancho_cucamonga_count = content.lower().count("rancho_cucamonga")
                # Allow some Rancho Cucamonga references in comments/docs
                rancho_cucamonga_ok = rancho_cucamonga_count <= 5

                if has_rancho and rancho_cucamonga_ok:
                    self._log_test(f"Transform: {file_path}", True, "Successfully updated to Rancho")
                else:
                    self._log_test(f"Transform: {file_path}", False, f"Rancho: {has_rancho}, Rancho Cucamonga count: {rancho_cucamonga_count}")

            except Exception as e:
                self._log_test(f"Transform: {file_path}", False, str(e))

    def _log_test(self, test_name: str, passed: bool, details: str = ""):
        """Log test result"""
        result = {
            "test": test_name,
            "passed": passed,
            "details": details
        }
        self.test_results.append(result)

        if passed:
            self.passed_tests += 1
            print(f"  ✅ {test_name}: {details}")
        else:
            self.failed_tests += 1
            print(f"  ❌ {test_name}: {details}")

    def _generate_validation_report(self) -> Dict:
        """Generate comprehensive validation report"""
        total_tests = len(self.test_results)
        pass_rate = (self.passed_tests / total_tests * 100) if total_tests > 0 else 0

        print("\n" + "=" * 60)
        print("🎯 RANCHO CUCAMONGA INTEGRATION VALIDATION COMPLETE")
        print("=" * 60)

        print(f"📊 Test Summary:")
        print(f"   • Total Tests: {total_tests}")
        print(f"   • Passed: {self.passed_tests}")
        print(f"   • Failed: {self.failed_tests}")
        print(f"   • Pass Rate: {pass_rate:.1f}%")

        if pass_rate >= 90:
            print("✅ EXCELLENT: Rancho Cucamonga integration successful!")
            status = "SUCCESS"
        elif pass_rate >= 75:
            print("⚠️  GOOD: Minor issues found, mostly working")
            status = "MOSTLY_SUCCESS"
        else:
            print("❌ ISSUES: Significant problems found")
            status = "NEEDS_WORK"

        print(f"\n🏠 Market Transition Summary:")
        print(f"   • Source: Rancho Cucamonga, CA → Target: Rancho Cucamonga, CA")
        print(f"   • Regulatory: TREC → California DRE")
        print(f"   • Price Ranges: Updated for California market")
        print(f"   • Neighborhoods: Rancho Cucamonga areas → Rancho neighborhoods")
        print(f"   • Compliance: Texas → California requirements")

        if self.failed_tests > 0:
            print(f"\n⚠️ Failed Tests:")
            for result in self.test_results:
                if not result["passed"]:
                    print(f"   • {result['test']}: {result['details']}")

        # Create detailed report
        report = {
            "validation_date": "2026-01-25",
            "market_transition": "Rancho Cucamonga TX → Rancho Cucamonga CA",
            "total_tests": total_tests,
            "passed_tests": self.passed_tests,
            "failed_tests": self.failed_tests,
            "pass_rate": pass_rate,
            "status": status,
            "test_results": self.test_results
        }

        # Save report
        report_path = project_root / "rancho_validation_report.json"
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)

        print(f"\n📄 Detailed report saved: {report_path}")

        return report


def main():
    """Run validation suite"""
    try:
        validator = RanchoMarketValidator()
        report = validator.run_all_validations()

        # Return appropriate exit code
        if report["status"] == "SUCCESS":
            sys.exit(0)
        elif report["status"] == "MOSTLY_SUCCESS":
            sys.exit(1)
        else:
            sys.exit(2)

    except Exception as e:
        print(f"❌ Validation failed with error: {e}")
        traceback.print_exc()
        sys.exit(3)


if __name__ == "__main__":
    main()