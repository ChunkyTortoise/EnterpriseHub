#!/usr/bin/env python3
"""
Service 6 Database Setup Validation Script

This script validates that the Service 6 database has been properly initialized
and all components are working correctly.

Usage:
    python database/validate_setup.py --db-url postgresql://user:pass@host:port/db
    
Environment variables:
    DATABASE_URL - PostgreSQL connection URL
    ENVIRONMENT - Deployment environment (development, staging, production)
"""

import os
import sys
import argparse
import asyncio
import asyncpg
from datetime import datetime
from typing import Dict, List, Any, Optional
import json

class DatabaseValidator:
    """Validates Service 6 database setup and configuration."""
    
    def __init__(self, db_url: str, environment: str = 'development'):
        self.db_url = db_url
        self.environment = environment
        self.connection: Optional[asyncpg.Connection] = None
        self.validation_results = []
        
    async def connect(self) -> bool:
        """Establish database connection."""
        try:
            self.connection = await asyncpg.connect(self.db_url)
            return True
        except Exception as e:
            print(f"❌ Database connection failed: {e}")
            return False
    
    async def disconnect(self):
        """Close database connection."""
        if self.connection:
            await self.connection.close()
    
    async def run_validation(self, category: str, name: str, query: str, expected_min: int = 1) -> Dict[str, Any]:
        """Run a validation query and return results."""
        try:
            result = await self.connection.fetch(query)
            count = len(result) if isinstance(result, list) else (result[0][0] if result else 0)
            
            status = "✅ PASS" if count >= expected_min else "❌ FAIL"
            
            validation = {
                'category': category,
                'name': name,
                'status': status,
                'count': count,
                'expected_min': expected_min,
                'details': result if len(str(result)) < 200 else f"{count} items found"
            }
            
            self.validation_results.append(validation)
            return validation
            
        except Exception as e:
            validation = {
                'category': category,
                'name': name,
                'status': "❌ ERROR",
                'count': 0,
                'expected_min': expected_min,
                'details': str(e)
            }
            self.validation_results.append(validation)
            return validation
    
    async def validate_schema(self):
        """Validate database schema components."""
        print("\n🔍 Validating Database Schema...")
        
        # Check tables
        await self.run_validation(
            "Schema", "Core Tables",
            "SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' AND table_type = 'BASE TABLE'",
            15
        )
        
        # Check indexes
        await self.run_validation(
            "Schema", "Performance Indexes",
            "SELECT indexname FROM pg_indexes WHERE schemaname = 'public' AND indexname LIKE 'idx_%'",
            40
        )
        
        # Check functions
        await self.run_validation(
            "Schema", "Custom Functions",
            "SELECT proname FROM pg_proc p JOIN pg_namespace n ON p.pronamespace = n.oid WHERE n.nspname = 'public'",
            8
        )
        
        # Check triggers
        await self.run_validation(
            "Schema", "Automated Triggers",
            "SELECT tgname FROM pg_trigger WHERE tgname NOT LIKE '%_oid'",
            10
        )
        
        # Check views
        await self.run_validation(
            "Schema", "Reporting Views",
            "SELECT table_name FROM information_schema.views WHERE table_schema = 'public'",
            5
        )
    
    async def validate_security(self):
        """Validate security configuration."""
        print("\n🔒 Validating Security Configuration...")
        
        # Check RLS policies
        await self.run_validation(
            "Security", "Row Level Security Policies",
            "SELECT policyname FROM pg_policies WHERE schemaname = 'public'",
            3
        )
        
        # Check roles
        await self.run_validation(
            "Security", "Database Roles",
            "SELECT rolname FROM pg_roles WHERE rolname LIKE 'service6_%'",
            5
        )
        
        # Check extensions
        await self.run_validation(
            "Security", "Required Extensions",
            "SELECT extname FROM pg_extension WHERE extname IN ('uuid-ossp', 'pgcrypto', 'btree_gin', 'pg_stat_statements')",
            4
        )
    
    async def validate_data_quality(self):
        """Validate data quality and integrity."""
        print("\n📊 Validating Data Quality...")
        
        # Check for data quality issues
        result = await self.connection.fetchrow("""
            SELECT COUNT(*) as invalid_count
            FROM leads
            WHERE email !~ '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\\.[A-Za-z]{2,}$'
               OR (phone IS NOT NULL AND phone !~ '^[0-9+\\-() ]{10,20}$')
        """)
        
        validation = {
            'category': 'Data Quality',
            'name': 'Lead Data Integrity',
            'status': "✅ PASS" if result['invalid_count'] == 0 else "⚠️ WARN",
            'count': result['invalid_count'],
            'expected_min': 0,
            'details': f"{result['invalid_count']} leads with invalid email/phone data"
        }
        self.validation_results.append(validation)
        
        # Check sample data (development only)
        if self.environment != 'production':
            await self.run_validation(
                "Data Quality", "Sample Data",
                "SELECT COUNT(*) FROM leads WHERE deleted_at IS NULL",
                5
            )
    
    async def validate_performance(self):
        """Validate performance configuration."""
        print("\n⚡ Validating Performance Configuration...")
        
        # Check materialized views
        await self.run_validation(
            "Performance", "Materialized Views",
            "SELECT matviewname FROM pg_matviews WHERE schemaname = 'public'",
            1
        )
        
        # Check for unused indexes
        result = await self.connection.fetch("""
            SELECT indexname 
            FROM pg_stat_user_indexes 
            WHERE idx_scan = 0 AND schemaname = 'public' AND indexname LIKE 'idx_%'
        """)
        
        validation = {
            'category': 'Performance',
            'name': 'Index Efficiency',
            'status': "✅ PASS" if len(result) <= 5 else "⚠️ WARN",
            'count': len(result),
            'expected_min': 0,
            'details': f"{len(result)} unused indexes found"
        }
        self.validation_results.append(validation)
    
    async def validate_compliance(self):
        """Validate GDPR and compliance features."""
        print("\n⚖️ Validating Compliance Configuration...")
        
        # Check audit logging
        await self.run_validation(
            "Compliance", "Audit Logging",
            "SELECT COUNT(*) FROM audit_log",
            0  # May be 0 in fresh database
        )
        
        # Check consent tracking structure
        await self.run_validation(
            "Compliance", "Consent Management",
            "SELECT column_name FROM information_schema.columns WHERE table_name = 'consent_logs'",
            10
        )
        
        # Check data retention policies
        await self.run_validation(
            "Compliance", "Data Retention Structure",
            "SELECT column_name FROM information_schema.columns WHERE table_name = 'data_retention'",
            8
        )
    
    async def run_application_tests(self):
        """Run application-specific validation tests."""
        print("\n🚀 Running Application Integration Tests...")
        
        # Test lead scoring function
        try:
            await self.connection.execute("SELECT calculate_lead_composite_score()")
            self.validation_results.append({
                'category': 'Application',
                'name': 'Lead Scoring Function',
                'status': '✅ PASS',
                'details': 'Function executes without error'
            })
        except Exception as e:
            self.validation_results.append({
                'category': 'Application',
                'name': 'Lead Scoring Function',
                'status': '❌ FAIL',
                'details': f'Function error: {e}'
            })
        
        # Test data retention function
        try:
            result = await self.connection.fetchrow("SELECT enforce_data_retention()")
            self.validation_results.append({
                'category': 'Application',
                'name': 'Data Retention Function',
                'status': '✅ PASS',
                'details': f'Processed {result[0]} retention policies'
            })
        except Exception as e:
            self.validation_results.append({
                'category': 'Application',
                'name': 'Data Retention Function',
                'status': '❌ FAIL',
                'details': f'Function error: {e}'
            })
        
        # Test schema health validation
        try:
            result = await self.connection.fetch("SELECT * FROM validate_schema_health()")
            passed = sum(1 for r in result if r['status'] == 'PASS')
            total = len(result)
            
            self.validation_results.append({
                'category': 'Application',
                'name': 'Schema Health Validation',
                'status': '✅ PASS' if passed == total else '⚠️ WARN',
                'details': f'{passed}/{total} health checks passed'
            })
        except Exception as e:
            self.validation_results.append({
                'category': 'Application',
                'name': 'Schema Health Validation',
                'status': '❌ FAIL',
                'details': f'Health check error: {e}'
            })
    
    async def run_all_validations(self):
        """Run complete validation suite."""
        print("🎯 Starting Service 6 Database Validation")
        print(f"📍 Environment: {self.environment}")
        print(f"🔗 Database URL: {self.db_url.split('@')[1] if '@' in self.db_url else 'localhost'}")
        
        if not await self.connect():
            return False
        
        try:
            await self.validate_schema()
            await self.validate_security()
            await self.validate_data_quality()
            await self.validate_performance()
            await self.validate_compliance()
            await self.run_application_tests()
            
            return True
            
        finally:
            await self.disconnect()
    
    def print_summary(self):
        """Print validation summary."""
        if not self.validation_results:
            print("❌ No validation results available")
            return
        
        # Group results by status
        passed = [r for r in self.validation_results if 'PASS' in r['status']]
        failed = [r for r in self.validation_results if 'FAIL' in r['status']]
        warnings = [r for r in self.validation_results if 'WARN' in r['status']]
        errors = [r for r in self.validation_results if 'ERROR' in r['status']]
        
        print(f"\n{'='*60}")
        print("📋 VALIDATION SUMMARY")
        print(f"{'='*60}")
        print(f"✅ Passed:   {len(passed)}")
        print(f"⚠️  Warnings: {len(warnings)}")
        print(f"❌ Failed:   {len(failed)}")
        print(f"🔥 Errors:   {len(errors)}")
        print(f"📊 Total:    {len(self.validation_results)}")
        
        # Print detailed results by category
        categories = {}
        for result in self.validation_results:
            cat = result['category']
            if cat not in categories:
                categories[cat] = []
            categories[cat].append(result)
        
        for category, results in categories.items():
            print(f"\n📂 {category.upper()}")
            print("-" * 40)
            for result in results:
                status_icon = result['status'].split()[0]
                print(f"{status_icon} {result['name']}")
                if 'FAIL' in result['status'] or 'ERROR' in result['status']:
                    print(f"   └─ {result['details']}")
        
        # Overall status
        overall_status = "✅ HEALTHY" if len(failed) == 0 and len(errors) == 0 else "❌ ISSUES DETECTED"
        print(f"\n🎯 OVERALL STATUS: {overall_status}")
        
        if len(failed) > 0 or len(errors) > 0:
            print("\n⚠️  ACTION REQUIRED:")
            for result in failed + errors:
                print(f"   • Fix {result['category']}: {result['name']}")
                print(f"     └─ {result['details']}")
        
        return len(failed) == 0 and len(errors) == 0

def main():
    """Main validation entry point."""
    parser = argparse.ArgumentParser(description='Validate Service 6 database setup')
    parser.add_argument('--db-url', default=os.getenv('DATABASE_URL'), 
                       help='PostgreSQL connection URL')
    parser.add_argument('--environment', default=os.getenv('ENVIRONMENT', 'development'),
                       choices=['development', 'staging', 'production'],
                       help='Deployment environment')
    parser.add_argument('--json', action='store_true',
                       help='Output results in JSON format')
    
    args = parser.parse_args()
    
    if not args.db_url:
        print("❌ Database URL required. Set DATABASE_URL environment variable or use --db-url")
        sys.exit(1)
    
    async def run_validation():
        validator = DatabaseValidator(args.db_url, args.environment)
        success = await validator.run_all_validations()
        
        if args.json:
            print(json.dumps(validator.validation_results, indent=2, default=str))
        else:
            healthy = validator.print_summary()
            if not healthy:
                sys.exit(1)
    
    asyncio.run(run_validation())

if __name__ == '__main__':
    main()
