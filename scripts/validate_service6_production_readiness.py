#!/usr/bin/env python3
"""
Service6 Production Readiness Validation Script
Validates all critical components before production deployment
"""

import os
import sys
import json
import subprocess
from pathlib import Path
from typing import Dict, List, Tuple

class ProductionValidator:
    """Validates Service6 production readiness"""
    
    def __init__(self):
        self.results: Dict[str, List[Tuple[str, bool, str]]] = {
            'security': [],
            'performance': [],
            'testing': [],
            'monitoring': [],
            'infrastructure': []
        }
        self.repo_root = Path(__file__).parent.parent
        
    def validate_security(self) -> None:
        """Validate security configuration"""
        print("\n=== SECURITY VALIDATION ===")
        
        # Check .env.service6 exists
        env_file = self.repo_root / '.env.service6'
        if env_file.exists():
            self.results['security'].append(
                ('.env.service6 exists', True, 'Production environment file configured')
            )
            
            # Check for placeholder values
            with open(env_file) as f:
                content = f.read()
                has_placeholders = 'YOUR_' in content
                self.results['security'].append(
                    ('No placeholder values', not has_placeholders, 
                     'All credentials configured' if not has_placeholders else 'CRITICAL: Configure actual credentials')
                )
        else:
            self.results['security'].append(
                ('.env.service6 exists', False, 'CRITICAL: Create production environment file')
            )
        
        # Check docker-compose has no secrets
        compose_file = self.repo_root / 'docker-compose.service6.yml'
        if compose_file.exists():
            with open(compose_file) as f:
                content = f.read()
                has_hardcoded = any(x in content for x in ['password:', 'api_key:', 'secret:'])
                self.results['security'].append(
                    ('No hardcoded secrets in docker-compose', not has_hardcoded,
                     'All secrets in environment' if not has_hardcoded else 'WARNING: Hardcoded secrets found')
                )
        
        # Check critical files not committed
        gitignore = self.repo_root / '.gitignore'
        if gitignore.exists():
            with open(gitignore) as f:
                content = f.read()
                secure_files = ['.env.service6', '.env.local', 'secrets/']
                all_ignored = all(f in content for f in secure_files)
                self.results['security'].append(
                    ('Sensitive files in .gitignore', all_ignored,
                     'Secrets protected' if all_ignored else 'WARNING: Add sensitive files to .gitignore')
                )
    
    def validate_performance(self) -> None:
        """Validate performance optimizations"""
        print("\n=== PERFORMANCE VALIDATION ===")
        
        # Check migration files exist
        migration_006 = self.repo_root / 'database/migrations/006_performance_critical_indexes.sql'
        self.results['performance'].append(
            ('Performance indexes migration exists', migration_006.exists(),
             'Ready to deploy' if migration_006.exists() else 'ERROR: Missing migration file')
        )
        
        # Check cache service implementation
        cache_service = self.repo_root / 'ghl_real_estate_ai/services/tiered_cache_service.py'
        self.results['performance'].append(
            ('Tiered cache service exists', cache_service.exists(),
             'Cache optimization ready' if cache_service.exists() else 'WARNING: Cache service missing')
        )
        
        # Check behavioral network service
        behavioral_network = self.repo_root / 'ghl_real_estate_ai/services/realtime_behavioral_network.py'
        if behavioral_network.exists():
            with open(behavioral_network) as f:
                content = f.read()
                line_count = len(content.split('\n'))
                self.results['performance'].append(
                    ('Behavioral network service (production-grade)', line_count > 2000,
                     f'{line_count} lines - Production ready' if line_count > 2000 else 'WARNING: Implementation incomplete')
                )
    
    def validate_testing(self) -> None:
        """Validate testing infrastructure"""
        print("\n=== TESTING VALIDATION ===")
        
        # Check integration tests exist
        integration_test = self.repo_root / 'tests/integration/test_service6_end_to_end.py'
        self.results['testing'].append(
            ('Integration test suite exists', integration_test.exists(),
             'End-to-end tests ready' if integration_test.exists() else 'ERROR: Missing integration tests')
        )
        
        # Check performance tests
        performance_dir = self.repo_root / 'tests/performance'
        has_perf_tests = performance_dir.exists() and any(performance_dir.glob('test_service6_*.py'))
        self.results['testing'].append(
            ('Performance test suite exists', has_perf_tests,
             'Load testing ready' if has_perf_tests else 'WARNING: Create performance tests')
        )
        
        # Check test configuration
        pytest_ini = self.repo_root / 'tests/pytest.ini'
        self.results['testing'].append(
            ('Pytest configuration exists', pytest_ini.exists(),
             'Test configuration ready' if pytest_ini.exists() else 'WARNING: Configure pytest')
        )
    
    def validate_monitoring(self) -> None:
        """Validate monitoring infrastructure"""
        print("\n=== MONITORING VALIDATION ===")
        
        # Check for monitoring configuration
        env_template = self.repo_root / '.env.service6.template'
        if env_template.exists():
            with open(env_template) as f:
                content = f.read()
                has_prometheus = 'PROMETHEUS' in content
                has_sentry = 'SENTRY' in content
                
                self.results['monitoring'].append(
                    ('Prometheus configuration', has_prometheus,
                     'Metrics collection configured' if has_prometheus else 'WARNING: Configure Prometheus')
                )
                self.results['monitoring'].append(
                    ('Sentry configuration', has_sentry,
                     'Error tracking configured' if has_sentry else 'WARNING: Configure Sentry')
                )
        
        # Check for health endpoints
        main_api = self.repo_root / 'ghl_real_estate_ai/api/main.py'
        if main_api.exists():
            with open(main_api) as f:
                content = f.read()
                has_health = '/health' in content
                self.results['monitoring'].append(
                    ('Health check endpoints', has_health,
                     'Health monitoring ready' if has_health else 'WARNING: Add health endpoints')
                )
    
    def validate_infrastructure(self) -> None:
        """Validate infrastructure configuration"""
        print("\n=== INFRASTRUCTURE VALIDATION ===")
        
        # Check docker-compose exists
        compose_file = self.repo_root / 'docker-compose.service6.yml'
        self.results['infrastructure'].append(
            ('Docker Compose configuration', compose_file.exists(),
             'Infrastructure as code ready' if compose_file.exists() else 'ERROR: Missing docker-compose')
        )
        
        # Check for database migrations directory
        migrations_dir = self.repo_root / 'database/migrations'
        migration_count = len(list(migrations_dir.glob('*.sql'))) if migrations_dir.exists() else 0
        self.results['infrastructure'].append(
            ('Database migrations', migration_count > 0,
             f'{migration_count} migrations ready' if migration_count > 0 else 'ERROR: No database migrations')
        )
        
        # Check for deployment scripts
        deploy_script = self.repo_root / 'scripts/deploy_service6_complete.py'
        self.results['infrastructure'].append(
            ('Deployment automation', deploy_script.exists(),
             'Automated deployment ready' if deploy_script.exists() else 'WARNING: Create deployment script')
        )
    
    def print_results(self) -> bool:
        """Print validation results and return overall status"""
        print("\n" + "="*80)
        print("SERVICE6 PRODUCTION READINESS VALIDATION REPORT")
        print("="*80)
        
        all_passed = True
        critical_failures = []
        warnings = []
        
        for category, checks in self.results.items():
            print(f"\n{category.upper()} ({len(checks)} checks):")
            print("-" * 80)
            
            for check_name, passed, message in checks:
                status = "✅ PASS" if passed else "❌ FAIL"
                print(f"{status}: {check_name}")
                print(f"        {message}")
                
                if not passed:
                    all_passed = False
                    if 'CRITICAL' in message or 'ERROR' in message:
                        critical_failures.append(f"{category}: {check_name} - {message}")
                    else:
                        warnings.append(f"{category}: {check_name} - {message}")
        
        # Summary
        print("\n" + "="*80)
        print("SUMMARY")
        print("="*80)
        
        total_checks = sum(len(checks) for checks in self.results.values())
        passed_checks = sum(1 for checks in self.results.values() for _, passed, _ in checks if passed)
        
        print(f"\nTotal Checks: {total_checks}")
        print(f"Passed: {passed_checks}")
        print(f"Failed: {total_checks - passed_checks}")
        print(f"\nSuccess Rate: {(passed_checks/total_checks)*100:.1f}%")
        
        if critical_failures:
            print("\n🚨 CRITICAL FAILURES (Must fix before deployment):")
            for failure in critical_failures:
                print(f"  - {failure}")
        
        if warnings:
            print("\n⚠️  WARNINGS (Recommended to fix):")
            for warning in warnings:
                print(f"  - {warning}")
        
        if all_passed:
            print("\n✅ ALL CHECKS PASSED - READY FOR PRODUCTION DEPLOYMENT")
        else:
            print("\n❌ VALIDATION FAILED - Address issues before deploying")
        
        # Production readiness percentage
        readiness = (passed_checks / total_checks) * 100
        print(f"\n📊 Production Readiness: {readiness:.1f}%")
        
        if readiness >= 95:
            print("   Status: EXCELLENT - Deploy with confidence")
        elif readiness >= 80:
            print("   Status: GOOD - Minor improvements needed")
        elif readiness >= 60:
            print("   Status: FAIR - Significant work required")
        else:
            print("   Status: NOT READY - Major improvements required")
        
        return all_passed
    
    def run_validation(self) -> int:
        """Run all validation checks"""
        print("Starting Service6 Production Readiness Validation...")
        
        self.validate_security()
        self.validate_performance()
        self.validate_testing()
        self.validate_monitoring()
        self.validate_infrastructure()
        
        success = self.print_results()
        
        return 0 if success else 1

if __name__ == '__main__':
    validator = ProductionValidator()
    sys.exit(validator.run_validation())
