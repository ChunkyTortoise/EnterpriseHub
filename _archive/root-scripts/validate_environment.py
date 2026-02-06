#!/usr/bin/env python3
"""
Environment Configuration Validation Script
Validates all required environment variables for deployment readiness

Business Impact: Ensures platform is properly configured before deployment
Author: Claude Code Agent - Configuration Specialist
Created: 2026-01-25
"""

import os
import sys
import json
from datetime import datetime
from typing import Dict, List, Tuple, Any, Optional
import re

# Try to load .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
    print("✅ Loaded .env file")
except ImportError:
    print("⚠️  python-dotenv not installed. Install with: pip install python-dotenv")
except Exception as e:
    print(f"⚠️  Could not load .env file: {e}")

class EnvironmentValidator:
    """Comprehensive environment configuration validator"""

    def __init__(self):
        self.results = {}
        self.overall_score = 0
        self.errors = []
        self.warnings = []
        self.critical_missing = []

    def validate_all(self) -> Dict[str, Any]:
        """Run comprehensive environment validation"""
        print("🔧 ENVIRONMENT CONFIGURATION VALIDATION")
        print("=" * 60)
        print()

        # Core validations
        self._validate_core_ai_providers()
        self._validate_ghl_integration()
        self._validate_database_config()
        self._validate_security_config()
        self._validate_optimization_config()
        self._validate_optional_services()

        # Generate final report
        return self._generate_final_report()

    def _validate_core_ai_providers(self):
        """Validate AI provider configurations"""
        print("🤖 Validating AI Provider Configuration...")

        critical_vars = [
            ('ANTHROPIC_API_KEY', self._validate_anthropic_key),
        ]

        optional_vars = [
            ('GOOGLE_API_KEY', self._validate_google_key),
            ('GEMINI_API_KEY', self._validate_google_key),
            ('PERPLEXITY_API_KEY', self._validate_generic_key),
        ]

        score = self._validate_variable_group("AI Providers", critical_vars, optional_vars)
        self.results['ai_providers'] = score

    def _validate_ghl_integration(self):
        """Validate GoHighLevel integration"""
        print("🏢 Validating GoHighLevel Integration...")

        critical_vars = [
            ('GHL_API_KEY', self._validate_ghl_key),
            ('GHL_LOCATION_ID', self._validate_location_id),
        ]

        optional_vars = [
            ('GHL_AGENCY_API_KEY', self._validate_ghl_key),
            ('GHL_AGENCY_ID', self._validate_generic_id),
            ('GHL_WEBHOOK_SECRET', self._validate_webhook_secret),
        ]

        score = self._validate_variable_group("GHL Integration", critical_vars, optional_vars)
        self.results['ghl_integration'] = score

    def _validate_database_config(self):
        """Validate database configuration"""
        print("🗄️  Validating Database Configuration...")

        critical_vars = [
            ('DATABASE_URL', self._validate_database_url),
        ]

        optional_vars = [
            ('REDIS_URL', self._validate_redis_url),
            ('REDIS_PASSWORD', self._validate_password),
            ('DB_POOL_SIZE', self._validate_positive_int),
            ('DB_MAX_OVERFLOW', self._validate_positive_int),
        ]

        score = self._validate_variable_group("Database", critical_vars, optional_vars)
        self.results['database'] = score

    def _validate_security_config(self):
        """Validate security configuration"""
        print("🔐 Validating Security Configuration...")

        critical_vars = [
            ('JWT_SECRET_KEY', self._validate_jwt_secret),
        ]

        optional_vars = [
            ('SESSION_SECRET_KEY', self._validate_session_secret),
        ]

        score = self._validate_variable_group("Security", critical_vars, optional_vars)
        self.results['security'] = score

    def _validate_optimization_config(self):
        """Validate optimization configuration"""
        print("⚡ Validating Optimization Configuration...")

        optimization_vars = [
            ('ENABLE_CONVERSATION_OPTIMIZATION', self._validate_boolean),
            ('ENABLE_ENHANCED_CACHING', self._validate_boolean),
            ('ENABLE_ASYNC_OPTIMIZATION', self._validate_boolean),
            ('ENABLE_TOKEN_BUDGET_ENFORCEMENT', self._validate_boolean),
            ('ENABLE_DATABASE_CONNECTION_POOLING', self._validate_boolean),
            ('ENABLE_SEMANTIC_RESPONSE_CACHING', self._validate_boolean),
            ('ENABLE_MULTI_TENANT_OPTIMIZATION', self._validate_boolean),
            ('ENABLE_ADVANCED_ANALYTICS', self._validate_boolean),
            ('ENABLE_COST_PREDICTION', self._validate_boolean),
        ]

        config_vars = [
            ('TOKEN_BUDGET_DEFAULT_MONTHLY', self._validate_positive_int),
            ('TOKEN_BUDGET_DEFAULT_DAILY', self._validate_positive_int),
            ('SEMANTIC_CACHE_SIMILARITY_THRESHOLD', self._validate_float_0_1),
            ('SEMANTIC_CACHE_TTL', self._validate_positive_int),
        ]

        score = self._validate_variable_group("Optimizations", optimization_vars, config_vars, all_optional=True)
        self.results['optimizations'] = score

    def _validate_optional_services(self):
        """Validate optional service configurations"""
        print("📡 Validating Optional Services...")

        optional_vars = [
            ('STRIPE_SECRET_KEY', self._validate_stripe_key),
            ('TWILIO_ACCOUNT_SID', self._validate_twilio_sid),
            ('SENDGRID_API_KEY', self._validate_sendgrid_key),
            ('VAPI_API_KEY', self._validate_generic_key),
            ('RETELL_API_KEY', self._validate_generic_key),
        ]

        score = self._validate_variable_group("Optional Services", [], optional_vars, all_optional=True)
        self.results['optional_services'] = score

    def _validate_variable_group(self, group_name: str, critical_vars: List[Tuple], optional_vars: List[Tuple], all_optional: bool = False) -> float:
        """Validate a group of environment variables"""
        total_score = 0
        max_score = len(critical_vars) + len(optional_vars)

        if max_score == 0:
            return 100.0

        # Validate critical variables
        for var_name, validator in critical_vars:
            value = os.getenv(var_name)
            if value:
                is_valid, message = validator(value) if validator else (True, "Present")
                if is_valid:
                    print(f"   ✅ {var_name}: {message}")
                    total_score += 1
                else:
                    print(f"   ❌ {var_name}: {message}")
                    if not all_optional:
                        self.critical_missing.append(var_name)
                        self.errors.append(f"Critical variable {var_name} invalid: {message}")
            else:
                print(f"   ❌ {var_name}: Not set")
                if not all_optional:
                    self.critical_missing.append(var_name)
                    self.errors.append(f"Critical variable {var_name} not set")

        # Validate optional variables
        for var_name, validator in optional_vars:
            value = os.getenv(var_name)
            if value:
                is_valid, message = validator(value) if validator else (True, "Present")
                if is_valid:
                    print(f"   ✅ {var_name}: {message}")
                    total_score += 1
                else:
                    print(f"   ⚠️  {var_name}: {message}")
                    self.warnings.append(f"Optional variable {var_name} invalid: {message}")
            else:
                print(f"   ➖ {var_name}: Not set (optional)")

        score = (total_score / max_score) * 100 if max_score > 0 else 100
        print(f"   📊 {group_name} Score: {score:.1f}% ({total_score}/{max_score})")
        print()
        return score

    # Validation functions
    def _validate_anthropic_key(self, value: str) -> Tuple[bool, str]:
        if not value.startswith('sk-ant-'):
            return False, "Invalid format (should start with 'sk-ant-')"
        if len(value) < 50:
            return False, "Too short for valid Anthropic key"
        return True, "Valid Anthropic API key format"

    def _validate_ghl_key(self, value: str) -> Tuple[bool, str]:
        if value.startswith('eyJ'):
            return True, "Valid JWT format"
        return False, "Invalid format (should be JWT starting with 'eyJ')"

    def _validate_google_key(self, value: str) -> Tuple[bool, str]:
        if len(value) < 30:
            return False, "Too short for valid Google API key"
        return True, "Valid Google API key format"

    def _validate_generic_key(self, value: str) -> Tuple[bool, str]:
        if len(value) < 10:
            return False, "Too short for API key"
        return True, "Present"

    def _validate_location_id(self, value: str) -> Tuple[bool, str]:
        if len(value) < 5:
            return False, "Too short for location ID"
        return True, "Valid location ID format"

    def _validate_generic_id(self, value: str) -> Tuple[bool, str]:
        if len(value) < 5:
            return False, "Too short for ID"
        return True, "Valid ID format"

    def _validate_database_url(self, value: str) -> Tuple[bool, str]:
        if not value.startswith(('postgresql://', 'postgres://')):
            return False, "Should start with postgresql:// or postgres://"
        return True, "Valid PostgreSQL URL format"

    def _validate_redis_url(self, value: str) -> Tuple[bool, str]:
        if not value.startswith('redis://'):
            return False, "Should start with redis://"
        return True, "Valid Redis URL format"

    def _validate_jwt_secret(self, value: str) -> Tuple[bool, str]:
        env = os.getenv('ENVIRONMENT', 'development')
        if env == 'production' and len(value) < 32:
            return False, "Must be at least 32 characters in production"
        if len(value) < 16:
            return False, "Should be at least 16 characters"
        return True, f"Valid JWT secret ({len(value)} chars)"

    def _validate_session_secret(self, value: str) -> Tuple[bool, str]:
        if len(value) < 32:
            return False, "Should be at least 32 characters"
        return True, f"Valid session secret ({len(value)} chars)"

    def _validate_password(self, value: str) -> Tuple[bool, str]:
        env = os.getenv('ENVIRONMENT', 'development')
        if env == 'production' and len(value) < 32:
            return False, "Should be at least 32 characters in production"
        return True, f"Password set ({len(value)} chars)"

    def _validate_webhook_secret(self, value: str) -> Tuple[bool, str]:
        if len(value) < 32:
            return False, "Should be at least 32 characters"
        return True, f"Valid webhook secret ({len(value)} chars)"

    def _validate_stripe_key(self, value: str) -> Tuple[bool, str]:
        if not value.startswith(('sk_test_', 'sk_live_')):
            return False, "Should start with sk_test_ or sk_live_"
        return True, "Valid Stripe key format"

    def _validate_twilio_sid(self, value: str) -> Tuple[bool, str]:
        if not value.startswith('AC'):
            return False, "Should start with 'AC'"
        return True, "Valid Twilio Account SID format"

    def _validate_sendgrid_key(self, value: str) -> Tuple[bool, str]:
        if not value.startswith('SG.'):
            return False, "Should start with 'SG.'"
        return True, "Valid SendGrid API key format"

    def _validate_boolean(self, value: str) -> Tuple[bool, str]:
        if value.lower() in ('true', 'false', '1', '0', 'yes', 'no'):
            return True, f"Set to '{value}'"
        return False, f"Invalid boolean value: {value}"

    def _validate_positive_int(self, value: str) -> Tuple[bool, str]:
        try:
            num = int(value)
            if num > 0:
                return True, f"Set to {num}"
            return False, "Should be positive integer"
        except ValueError:
            return False, "Should be integer"

    def _validate_float_0_1(self, value: str) -> Tuple[bool, str]:
        try:
            num = float(value)
            if 0 <= num <= 1:
                return True, f"Set to {num}"
            return False, "Should be between 0 and 1"
        except ValueError:
            return False, "Should be float"

    def _generate_final_report(self) -> Dict[str, Any]:
        """Generate comprehensive validation report"""
        print("📊 ENVIRONMENT VALIDATION REPORT")
        print("=" * 60)
        print()

        # Calculate overall score
        if self.results:
            self.overall_score = sum(self.results.values()) / len(self.results)
        else:
            self.overall_score = 0

        # Print category scores
        print("📋 CATEGORY SCORES:")
        for category, score in self.results.items():
            status_icon = "✅" if score >= 80 else "⚠️" if score >= 60 else "❌"
            print(f"   {status_icon} {category.replace('_', ' ').title()}: {score:.1f}%")
        print()

        # Overall assessment
        print(f"🎯 OVERALL SCORE: {self.overall_score:.1f}%")

        if self.overall_score >= 90:
            status = "🏆 EXCELLENT - Ready for production deployment"
            deployment_ready = True
        elif self.overall_score >= 75:
            status = "✅ GOOD - Ready with minor improvements"
            deployment_ready = True
        elif self.overall_score >= 60:
            status = "⚠️ FAIR - Needs configuration updates"
            deployment_ready = False
        else:
            status = "❌ POOR - Major configuration issues"
            deployment_ready = False

        print(f"📊 STATUS: {status}")
        print()

        # Critical issues
        if self.critical_missing:
            print("🚨 CRITICAL MISSING VARIABLES:")
            for var in self.critical_missing:
                print(f"   • {var}")
            print()

        # Errors and warnings
        if self.errors:
            print("❌ ERRORS:")
            for error in self.errors[:5]:  # Show first 5
                print(f"   • {error}")
            if len(self.errors) > 5:
                print(f"   ... and {len(self.errors) - 5} more")
            print()

        if self.warnings:
            print("⚠️  WARNINGS:")
            for warning in self.warnings[:5]:  # Show first 5
                print(f"   • {warning}")
            if len(self.warnings) > 5:
                print(f"   ... and {len(self.warnings) - 5} more")
            print()

        # Next steps
        print("🔄 NEXT STEPS:")
        if deployment_ready:
            print("   1. ✅ Environment configuration is deployment-ready")
            print("   2. 🚀 Run: streamlit run app.py")
            print("   3. 🔍 Monitor application logs for any runtime issues")
            if self.warnings:
                print("   4. ⚠️  Consider addressing warnings for optimal performance")
        else:
            print("   1. ❌ Fix critical missing variables listed above")
            print("   2. 📝 Update your .env file with required values")
            print("   3. 🔄 Run this script again to verify")
            print("   4. 📚 See .env.example for complete template")

        print()

        # Generate report file
        report_data = {
            'timestamp': datetime.now().isoformat(),
            'overall_score': self.overall_score,
            'deployment_ready': deployment_ready,
            'category_scores': self.results,
            'critical_missing': self.critical_missing,
            'errors': self.errors,
            'warnings': self.warnings,
            'status': status
        }

        report_filename = f"environment_validation_report_{int(datetime.now().timestamp())}.json"
        with open(report_filename, 'w') as f:
            json.dump(report_data, f, indent=2)
        print(f"📄 Detailed report saved to: {report_filename}")
        print()

        if deployment_ready:
            print("✅ VALIDATION PASSED - Environment is deployment-ready!")
        else:
            print("❌ VALIDATION FAILED - Fix critical issues before deployment")

        return report_data

def main():
    """Main entry point"""
    validator = EnvironmentValidator()
    result = validator.validate_all()

    # Exit with error code if not deployment ready
    if not result.get('deployment_ready', False):
        sys.exit(1)
    else:
        sys.exit(0)

if __name__ == "__main__":
    main()