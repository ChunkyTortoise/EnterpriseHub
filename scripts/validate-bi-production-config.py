#!/usr/bin/env python3
"""
Jorge's BI Dashboard Production Configuration Validator.

Validates production environment configuration for security, completeness,
and compliance with production deployment requirements.

Author: Claude Sonnet 4
Date: 2026-01-25
Usage: python scripts/validate-bi-production-config.py
"""

import os
import re
import sys
import json
import base64
import argparse
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from urllib.parse import urlparse

# ANSI Color codes for output
class Colors:
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    PURPLE = '\033[95m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    END = '\033[0m'

@dataclass
class ValidationResult:
    """Represents a single validation check result."""
    category: str
    item: str
    status: str  # 'pass', 'fail', 'warning', 'info'
    message: str
    severity: str = 'medium'  # 'low', 'medium', 'high', 'critical'

class ProductionConfigValidator:
    """Validates production configuration for Jorge's BI Dashboard."""

    def __init__(self, config_path: str = None):
        self.config_path = config_path or ".env.bi.production"
        self.config = {}
        self.results: List[ValidationResult] = []

        # Load configuration
        self.load_config()

    def load_config(self):
        """Load environment configuration."""
        if not os.path.exists(self.config_path):
            self.results.append(ValidationResult(
                "Configuration", "File Existence", "fail",
                f"Configuration file not found: {self.config_path}",
                "critical"
            ))
            return

        try:
            with open(self.config_path, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        self.config[key.strip()] = value.strip()

            self.results.append(ValidationResult(
                "Configuration", "File Loading", "pass",
                f"Successfully loaded {len(self.config)} configuration variables"
            ))
        except Exception as e:
            self.results.append(ValidationResult(
                "Configuration", "File Loading", "fail",
                f"Error loading configuration: {e}",
                "critical"
            ))

    def validate_environment_basics(self):
        """Validate basic environment configuration."""
        required_basics = {
            'ENVIRONMENT': 'production',
            'SERVICE_NAME': 'jorge-bi-dashboard',
            'DEBUG': 'false',
            'LOG_LEVEL': ['INFO', 'WARN', 'ERROR']
        }

        for key, expected in required_basics.items():
            value = self.config.get(key)

            if not value:
                self.results.append(ValidationResult(
                    "Environment", key, "fail",
                    f"Required environment variable missing: {key}",
                    "high"
                ))
            elif isinstance(expected, list):
                if value not in expected:
                    self.results.append(ValidationResult(
                        "Environment", key, "warning",
                        f"{key} value '{value}' not in recommended values: {expected}",
                        "medium"
                    ))
                else:
                    self.results.append(ValidationResult(
                        "Environment", key, "pass",
                        f"{key} correctly set to '{value}'"
                    ))
            elif value != expected:
                self.results.append(ValidationResult(
                    "Environment", key, "fail",
                    f"{key} must be '{expected}' in production, got '{value}'",
                    "high"
                ))
            else:
                self.results.append(ValidationResult(
                    "Environment", key, "pass",
                    f"{key} correctly set to '{value}'"
                ))

    def validate_database_config(self):
        """Validate database configuration."""
        db_url = self.config.get('DATABASE_URL')
        read_db_url = self.config.get('DATABASE_READ_URL')

        if not db_url:
            self.results.append(ValidationResult(
                "Database", "Primary Connection", "fail",
                "DATABASE_URL is required for production",
                "critical"
            ))
        else:
            # Parse database URL
            try:
                parsed = urlparse(db_url)

                # Check for SSL requirement
                if 'sslmode=require' not in db_url:
                    self.results.append(ValidationResult(
                        "Database", "SSL Configuration", "fail",
                        "DATABASE_URL must include 'sslmode=require' in production",
                        "high"
                    ))
                else:
                    self.results.append(ValidationResult(
                        "Database", "SSL Configuration", "pass",
                        "SSL mode correctly configured for production"
                    ))

                # Check for production database name
                if 'production' not in parsed.path:
                    self.results.append(ValidationResult(
                        "Database", "Database Name", "warning",
                        "Database name should contain 'production' for clarity",
                        "low"
                    ))

                self.results.append(ValidationResult(
                    "Database", "Primary Connection", "pass",
                    "Database URL format is valid"
                ))

            except Exception as e:
                self.results.append(ValidationResult(
                    "Database", "Primary Connection", "fail",
                    f"Invalid DATABASE_URL format: {e}",
                    "high"
                ))

        # Check read replica
        if not read_db_url:
            self.results.append(ValidationResult(
                "Database", "Read Replica", "warning",
                "DATABASE_READ_URL not configured - consider for performance",
                "medium"
            ))
        else:
            self.results.append(ValidationResult(
                "Database", "Read Replica", "pass",
                "Read replica configured for analytics queries"
            ))

        # Check pool configuration
        pool_configs = {
            'DB_POOL_SIZE': (10, 50),
            'DB_MAX_OVERFLOW': (20, 100),
            'DB_POOL_TIMEOUT': (10, 60)
        }

        for config_key, (min_val, max_val) in pool_configs.items():
            value = self.config.get(config_key)
            if value:
                try:
                    int_value = int(value)
                    if min_val <= int_value <= max_val:
                        self.results.append(ValidationResult(
                            "Database", config_key, "pass",
                            f"{config_key} appropriately set to {int_value}"
                        ))
                    else:
                        self.results.append(ValidationResult(
                            "Database", config_key, "warning",
                            f"{config_key} value {int_value} outside recommended range {min_val}-{max_val}",
                            "medium"
                        ))
                except ValueError:
                    self.results.append(ValidationResult(
                        "Database", config_key, "fail",
                        f"{config_key} must be a valid integer",
                        "medium"
                    ))

    def validate_redis_config(self):
        """Validate Redis cache configuration."""
        redis_url = self.config.get('REDIS_URL')

        if not redis_url:
            self.results.append(ValidationResult(
                "Redis", "Connection URL", "fail",
                "REDIS_URL is required for production caching",
                "critical"
            ))
            return

        # Check for authentication
        if 'default:' not in redis_url and '@' not in redis_url:
            self.results.append(ValidationResult(
                "Redis", "Authentication", "fail",
                "Redis must have authentication enabled in production",
                "high"
            ))
        else:
            self.results.append(ValidationResult(
                "Redis", "Authentication", "pass",
                "Redis authentication configured"
            ))

        # Check cluster configuration
        cluster_nodes = self.config.get('REDIS_CLUSTER_NODES')
        if cluster_nodes:
            node_count = len(cluster_nodes.split(','))
            if node_count >= 3:
                self.results.append(ValidationResult(
                    "Redis", "Cluster Configuration", "pass",
                    f"Redis cluster with {node_count} nodes configured"
                ))
            else:
                self.results.append(ValidationResult(
                    "Redis", "Cluster Configuration", "warning",
                    f"Redis cluster has only {node_count} nodes - recommend at least 3",
                    "medium"
                ))

        # Validate cache TTL settings
        cache_ttls = {
            'CACHE_TTL_DASHBOARD': (60, 600),
            'CACHE_TTL_REVENUE': (300, 1800),
            'CACHE_TTL_BOT_PERFORMANCE': (60, 300)
        }

        for ttl_key, (min_ttl, max_ttl) in cache_ttls.items():
            ttl_value = self.config.get(ttl_key)
            if ttl_value:
                try:
                    ttl_int = int(ttl_value)
                    if min_ttl <= ttl_int <= max_ttl:
                        self.results.append(ValidationResult(
                            "Redis", ttl_key, "pass",
                            f"TTL appropriately set to {ttl_int} seconds"
                        ))
                    else:
                        self.results.append(ValidationResult(
                            "Redis", ttl_key, "warning",
                            f"TTL {ttl_int} outside recommended range {min_ttl}-{max_ttl}",
                            "low"
                        ))
                except ValueError:
                    self.results.append(ValidationResult(
                        "Redis", ttl_key, "fail",
                        f"{ttl_key} must be a valid integer",
                        "medium"
                    ))

    def validate_ai_services(self):
        """Validate AI service configuration."""
        anthropic_key = self.config.get('ANTHROPIC_API_KEY')

        if not anthropic_key:
            self.results.append(ValidationResult(
                "AI Services", "Anthropic API Key", "fail",
                "ANTHROPIC_API_KEY is required for production",
                "critical"
            ))
        elif anthropic_key.startswith('${'):
            self.results.append(ValidationResult(
                "AI Services", "Anthropic API Key", "warning",
                "ANTHROPIC_API_KEY appears to be a placeholder - replace with actual key",
                "high"
            ))
        elif not anthropic_key.startswith('sk-ant-'):
            self.results.append(ValidationResult(
                "AI Services", "Anthropic API Key", "fail",
                "ANTHROPIC_API_KEY format appears invalid (should start with 'sk-ant-')",
                "high"
            ))
        else:
            self.results.append(ValidationResult(
                "AI Services", "Anthropic API Key", "pass",
                "Anthropic API key format appears valid"
            ))

        # Check model configuration
        model = self.config.get('ANTHROPIC_MODEL', '')
        if 'claude-3' not in model:
            self.results.append(ValidationResult(
                "AI Services", "Model Configuration", "warning",
                f"Consider using Claude 3 model for production (current: {model})",
                "low"
            ))

        # Check timeout configuration
        timeout = self.config.get('ANTHROPIC_TIMEOUT')
        if timeout:
            try:
                timeout_int = int(timeout)
                if timeout_int < 10 or timeout_int > 60:
                    self.results.append(ValidationResult(
                        "AI Services", "API Timeout", "warning",
                        f"API timeout {timeout_int}s may be too {'low' if timeout_int < 10 else 'high'}",
                        "medium"
                    ))
                else:
                    self.results.append(ValidationResult(
                        "AI Services", "API Timeout", "pass",
                        f"API timeout appropriately set to {timeout_int}s"
                    ))
            except ValueError:
                self.results.append(ValidationResult(
                    "AI Services", "API Timeout", "fail",
                    "ANTHROPIC_TIMEOUT must be a valid integer",
                    "medium"
                ))

    def validate_security_config(self):
        """Validate security configuration."""
        # JWT Secret validation
        jwt_secret = self.config.get('JWT_SECRET_KEY')
        if not jwt_secret:
            self.results.append(ValidationResult(
                "Security", "JWT Secret", "fail",
                "JWT_SECRET_KEY is required for authentication",
                "critical"
            ))
        elif jwt_secret.startswith('${'):
            self.results.append(ValidationResult(
                "Security", "JWT Secret", "fail",
                "JWT_SECRET_KEY appears to be a placeholder - replace with actual secret",
                "critical"
            ))
        elif len(jwt_secret) < 32:
            self.results.append(ValidationResult(
                "Security", "JWT Secret", "fail",
                f"JWT_SECRET_KEY too short ({len(jwt_secret)} chars) - minimum 32 characters required",
                "high"
            ))
        else:
            self.results.append(ValidationResult(
                "Security", "JWT Secret", "pass",
                f"JWT secret length appropriate ({len(jwt_secret)} chars)"
            ))

        # Encryption key validation
        encryption_key = self.config.get('DATA_ENCRYPTION_KEY')
        if not encryption_key:
            self.results.append(ValidationResult(
                "Security", "Encryption Key", "warning",
                "DATA_ENCRYPTION_KEY not set - consider for PII protection",
                "medium"
            ))
        elif len(encryption_key) != 64:  # 32 bytes in hex = 64 characters
            self.results.append(ValidationResult(
                "Security", "Encryption Key", "fail",
                "DATA_ENCRYPTION_KEY must be exactly 64 characters (32 bytes hex)",
                "high"
            ))
        else:
            self.results.append(ValidationResult(
                "Security", "Encryption Key", "pass",
                "Encryption key length is correct"
            ))

        # CORS validation
        cors_origins = self.config.get('CORS_ORIGINS', '')
        if 'localhost' in cors_origins or '127.0.0.1' in cors_origins:
            self.results.append(ValidationResult(
                "Security", "CORS Configuration", "fail",
                "CORS_ORIGINS contains localhost/127.0.0.1 - not allowed in production",
                "high"
            ))
        elif not cors_origins or cors_origins.startswith('${'):
            self.results.append(ValidationResult(
                "Security", "CORS Configuration", "warning",
                "CORS_ORIGINS not properly configured",
                "medium"
            ))
        else:
            self.results.append(ValidationResult(
                "Security", "CORS Configuration", "pass",
                "CORS origins appear properly configured"
            ))

        # Rate limiting
        rate_limit = self.config.get('API_RATE_LIMIT')
        if rate_limit:
            try:
                limit_int = int(rate_limit)
                if limit_int < 100:
                    self.results.append(ValidationResult(
                        "Security", "Rate Limiting", "warning",
                        f"Rate limit {limit_int} may be too restrictive for production",
                        "low"
                    ))
                elif limit_int > 10000:
                    self.results.append(ValidationResult(
                        "Security", "Rate Limiting", "warning",
                        f"Rate limit {limit_int} may be too permissive",
                        "medium"
                    ))
                else:
                    self.results.append(ValidationResult(
                        "Security", "Rate Limiting", "pass",
                        f"Rate limiting appropriately configured ({limit_int}/hour)"
                    ))
            except ValueError:
                self.results.append(ValidationResult(
                    "Security", "Rate Limiting", "fail",
                    "API_RATE_LIMIT must be a valid integer",
                    "medium"
                ))

    def validate_ghl_integration(self):
        """Validate GoHighLevel integration configuration."""
        location_id = self.config.get('GHL_LOCATION_ID')
        api_key = self.config.get('GHL_API_KEY')
        webhook_secret = self.config.get('GHL_WEBHOOK_SECRET')

        if not location_id:
            self.results.append(ValidationResult(
                "GHL Integration", "Location ID", "fail",
                "GHL_LOCATION_ID is required for Jorge's platform",
                "critical"
            ))
        elif location_id.startswith('${'):
            self.results.append(ValidationResult(
                "GHL Integration", "Location ID", "fail",
                "GHL_LOCATION_ID appears to be a placeholder - replace with Jorge's actual location ID",
                "critical"
            ))
        else:
            self.results.append(ValidationResult(
                "GHL Integration", "Location ID", "pass",
                "GHL location ID is configured"
            ))

        if not api_key:
            self.results.append(ValidationResult(
                "GHL Integration", "API Key", "fail",
                "GHL_API_KEY is required for platform integration",
                "critical"
            ))
        elif api_key.startswith('${'):
            self.results.append(ValidationResult(
                "GHL Integration", "API Key", "fail",
                "GHL_API_KEY appears to be a placeholder - replace with Jorge's actual API key",
                "critical"
            ))
        elif not (api_key.startswith('eyJ') and len(api_key) > 100):
            self.results.append(ValidationResult(
                "GHL Integration", "API Key", "warning",
                "GHL_API_KEY format may be invalid (should be JWT format)",
                "medium"
            ))
        else:
            self.results.append(ValidationResult(
                "GHL Integration", "API Key", "pass",
                "GHL API key format appears valid"
            ))

        if not webhook_secret:
            self.results.append(ValidationResult(
                "GHL Integration", "Webhook Secret", "fail",
                "GHL_WEBHOOK_SECRET is required for secure webhook verification",
                "high"
            ))
        elif webhook_secret.startswith('${'):
            self.results.append(ValidationResult(
                "GHL Integration", "Webhook Secret", "fail",
                "GHL_WEBHOOK_SECRET appears to be a placeholder - generate actual secret",
                "high"
            ))
        elif len(webhook_secret) < 32:
            self.results.append(ValidationResult(
                "GHL Integration", "Webhook Secret", "fail",
                f"GHL_WEBHOOK_SECRET too short ({len(webhook_secret)} chars) - minimum 32 characters",
                "high"
            ))
        else:
            self.results.append(ValidationResult(
                "GHL Integration", "Webhook Secret", "pass",
                "GHL webhook secret length is appropriate"
            ))

    def validate_performance_config(self):
        """Validate performance and scaling configuration."""
        # WebSocket limits
        ws_max_connections = self.config.get('WS_MAX_CONNECTIONS')
        if ws_max_connections:
            try:
                connections_int = int(ws_max_connections)
                if connections_int < 100:
                    self.results.append(ValidationResult(
                        "Performance", "WebSocket Connections", "warning",
                        f"Max WebSocket connections {connections_int} may be too low for production",
                        "medium"
                    ))
                elif connections_int > 10000:
                    self.results.append(ValidationResult(
                        "Performance", "WebSocket Connections", "warning",
                        f"Max WebSocket connections {connections_int} requires significant resources",
                        "low"
                    ))
                else:
                    self.results.append(ValidationResult(
                        "Performance", "WebSocket Connections", "pass",
                        f"WebSocket connection limit appropriately set ({connections_int})"
                    ))
            except ValueError:
                self.results.append(ValidationResult(
                    "Performance", "WebSocket Connections", "fail",
                    "WS_MAX_CONNECTIONS must be a valid integer",
                    "medium"
                ))

        # ML Performance
        ml_timeout = self.config.get('ML_PREDICTION_TIMEOUT')
        if ml_timeout:
            try:
                timeout_int = int(ml_timeout)
                if timeout_int < 1:
                    self.results.append(ValidationResult(
                        "Performance", "ML Timeout", "fail",
                        "ML_PREDICTION_TIMEOUT too low - may cause failures",
                        "medium"
                    ))
                elif timeout_int > 30:
                    self.results.append(ValidationResult(
                        "Performance", "ML Timeout", "warning",
                        f"ML_PREDICTION_TIMEOUT {timeout_int}s may be too high for real-time use",
                        "low"
                    ))
                else:
                    self.results.append(ValidationResult(
                        "Performance", "ML Timeout", "pass",
                        f"ML prediction timeout appropriately set ({timeout_int}s)"
                    ))
            except ValueError:
                self.results.append(ValidationResult(
                    "Performance", "ML Timeout", "fail",
                    "ML_PREDICTION_TIMEOUT must be a valid integer",
                    "medium"
                ))

        # Scaling configuration
        min_replicas = self.config.get('MIN_REPLICAS')
        max_replicas = self.config.get('MAX_REPLICAS')

        if min_replicas and max_replicas:
            try:
                min_int = int(min_replicas)
                max_int = int(max_replicas)

                if min_int < 2:
                    self.results.append(ValidationResult(
                        "Performance", "Scaling Configuration", "warning",
                        f"MIN_REPLICAS {min_int} less than 2 - no redundancy",
                        "medium"
                    ))
                elif min_int >= max_int:
                    self.results.append(ValidationResult(
                        "Performance", "Scaling Configuration", "fail",
                        f"MIN_REPLICAS {min_int} >= MAX_REPLICAS {max_int}",
                        "high"
                    ))
                else:
                    self.results.append(ValidationResult(
                        "Performance", "Scaling Configuration", "pass",
                        f"Scaling configured for {min_int}-{max_int} replicas"
                    ))
            except ValueError:
                self.results.append(ValidationResult(
                    "Performance", "Scaling Configuration", "fail",
                    "MIN_REPLICAS and MAX_REPLICAS must be valid integers",
                    "medium"
                ))

    def validate_monitoring_config(self):
        """Validate monitoring and observability configuration."""
        # Check monitoring enabled
        metrics_enabled = self.config.get('ENABLE_METRICS', '').lower()
        if metrics_enabled != 'true':
            self.results.append(ValidationResult(
                "Monitoring", "Metrics Collection", "warning",
                "ENABLE_METRICS should be 'true' in production for observability",
                "medium"
            ))
        else:
            self.results.append(ValidationResult(
                "Monitoring", "Metrics Collection", "pass",
                "Metrics collection enabled"
            ))

        # Check Prometheus configuration
        prometheus_enabled = self.config.get('PROMETHEUS_ENABLED', '').lower()
        if prometheus_enabled == 'true':
            self.results.append(ValidationResult(
                "Monitoring", "Prometheus", "pass",
                "Prometheus monitoring enabled"
            ))

            # Check metrics path
            metrics_path = self.config.get('PROMETHEUS_METRICS_PATH', '/metrics')
            if not metrics_path.startswith('/'):
                self.results.append(ValidationResult(
                    "Monitoring", "Metrics Path", "fail",
                    "PROMETHEUS_METRICS_PATH must start with '/'",
                    "medium"
                ))
        else:
            self.results.append(ValidationResult(
                "Monitoring", "Prometheus", "warning",
                "Prometheus monitoring not enabled - recommended for production",
                "medium"
            ))

        # Check logging configuration
        log_format = self.config.get('LOG_FORMAT', '')
        if log_format != 'json':
            self.results.append(ValidationResult(
                "Monitoring", "Log Format", "warning",
                "LOG_FORMAT should be 'json' for structured logging in production",
                "low"
            ))
        else:
            self.results.append(ValidationResult(
                "Monitoring", "Log Format", "pass",
                "Structured JSON logging configured"
            ))

        # Check retention policies
        log_retention = self.config.get('LOG_RETENTION_DAYS')
        if log_retention:
            try:
                retention_int = int(log_retention)
                if retention_int < 7:
                    self.results.append(ValidationResult(
                        "Monitoring", "Log Retention", "warning",
                        f"Log retention {retention_int} days may be too short",
                        "low"
                    ))
                elif retention_int > 90:
                    self.results.append(ValidationResult(
                        "Monitoring", "Log Retention", "warning",
                        f"Log retention {retention_int} days may consume excessive storage",
                        "low"
                    ))
                else:
                    self.results.append(ValidationResult(
                        "Monitoring", "Log Retention", "pass",
                        f"Log retention appropriately set to {retention_int} days"
                    ))
            except ValueError:
                self.results.append(ValidationResult(
                    "Monitoring", "Log Retention", "fail",
                    "LOG_RETENTION_DAYS must be a valid integer",
                    "medium"
                ))

    def validate_feature_flags(self):
        """Validate feature flag configuration."""
        feature_flags = {
            'ENABLE_PREDICTIVE_INSIGHTS': 'true',
            'ENABLE_REAL_TIME_STREAMING': 'true',
            'ENABLE_ADVANCED_ANALYTICS': 'true',
            'ENABLE_AI_CONCIERGE': 'true'
        }

        for flag, recommended in feature_flags.items():
            value = self.config.get(flag, '').lower()
            if value != recommended:
                self.results.append(ValidationResult(
                    "Features", flag, "warning",
                    f"{flag} should be '{recommended}' for full BI functionality",
                    "low"
                ))
            else:
                self.results.append(ValidationResult(
                    "Features", flag, "pass",
                    f"{flag} properly enabled"
                ))

        # Check debug features are disabled
        debug_features = [
            'ENABLE_DEBUG_ENDPOINTS',
            'ENABLE_PERFORMANCE_PROFILING'
        ]

        for flag in debug_features:
            value = self.config.get(flag, '').lower()
            if value == 'true':
                self.results.append(ValidationResult(
                    "Features", flag, "fail",
                    f"{flag} must be 'false' in production for security",
                    "high"
                ))
            else:
                self.results.append(ValidationResult(
                    "Features", flag, "pass",
                    f"{flag} correctly disabled for production"
                ))

    def print_results(self):
        """Print validation results in a formatted manner."""
        print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*80}{Colors.END}")
        print(f"{Colors.BOLD}{Colors.BLUE}JORGE'S BI DASHBOARD - PRODUCTION CONFIG VALIDATION{Colors.END}")
        print(f"{Colors.BOLD}{Colors.BLUE}{'='*80}{Colors.END}\n")

        # Group results by category
        categories = {}
        for result in self.results:
            if result.category not in categories:
                categories[result.category] = []
            categories[result.category].append(result)

        # Count totals
        totals = {'pass': 0, 'fail': 0, 'warning': 0, 'info': 0}
        critical_issues = 0
        high_issues = 0

        for result in self.results:
            totals[result.status] += 1
            if result.severity == 'critical':
                critical_issues += 1
            elif result.severity == 'high':
                high_issues += 1

        # Print summary
        print(f"{Colors.BOLD}VALIDATION SUMMARY:{Colors.END}")
        print(f"  {Colors.GREEN}✅ Passed:{Colors.END} {totals['pass']}")
        print(f"  {Colors.YELLOW}⚠️  Warnings:{Colors.END} {totals['warning']}")
        print(f"  {Colors.RED}❌ Failed:{Colors.END} {totals['fail']}")
        print(f"  {Colors.BLUE}ℹ️  Info:{Colors.END} {totals['info']}")
        print(f"  {Colors.PURPLE}🚨 Critical Issues:{Colors.END} {critical_issues}")
        print(f"  {Colors.PURPLE}⚠️  High Priority:{Colors.END} {high_issues}")
        print()

        # Print results by category
        for category, results in categories.items():
            print(f"{Colors.BOLD}{Colors.CYAN}{category.upper()}:{Colors.END}")

            for result in results:
                status_color = {
                    'pass': Colors.GREEN,
                    'fail': Colors.RED,
                    'warning': Colors.YELLOW,
                    'info': Colors.BLUE
                }.get(result.status, Colors.WHITE)

                status_icon = {
                    'pass': '✅',
                    'fail': '❌',
                    'warning': '⚠️',
                    'info': 'ℹ️'
                }.get(result.status, '?')

                severity_indicator = {
                    'critical': f"{Colors.PURPLE}🚨{Colors.END}",
                    'high': f"{Colors.RED}⚠️{Colors.END}",
                    'medium': f"{Colors.YELLOW}⚠️{Colors.END}",
                    'low': f"{Colors.BLUE}ℹ️{Colors.END}"
                }.get(result.severity, '')

                print(f"  {status_color}{status_icon}{Colors.END} {severity_indicator} "
                      f"{result.item}: {result.message}")

            print()

        # Production readiness assessment
        print(f"{Colors.BOLD}{Colors.BLUE}{'='*80}{Colors.END}")
        print(f"{Colors.BOLD}PRODUCTION READINESS ASSESSMENT:{Colors.END}\n")

        if critical_issues > 0:
            print(f"{Colors.RED}🚫 NOT READY FOR PRODUCTION{Colors.END}")
            print(f"   Critical issues must be resolved: {critical_issues}")
        elif high_issues > 0:
            print(f"{Colors.YELLOW}⚠️  CONDITIONAL DEPLOYMENT{Colors.END}")
            print(f"   High priority issues should be addressed: {high_issues}")
        elif totals['fail'] > 0:
            print(f"{Colors.YELLOW}⚠️  DEPLOYMENT WITH CAUTION{Colors.END}")
            print(f"   Some configuration issues detected: {totals['fail']}")
        else:
            print(f"{Colors.GREEN}✅ READY FOR PRODUCTION{Colors.END}")
            print("   Configuration validation passed!")

        print(f"\n{Colors.BOLD}NEXT STEPS:{Colors.END}")
        if critical_issues > 0 or high_issues > 0:
            print(f"1. {Colors.RED}Fix critical and high priority issues{Colors.END}")
            print("2. Re-run validation")
            print("3. Proceed with deployment only after all issues resolved")
        else:
            print("1. Apply configuration to production environment")
            print("2. Run deployment scripts")
            print("3. Perform post-deployment validation")

        print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*80}{Colors.END}")

        return critical_issues == 0 and high_issues == 0

    def run_validation(self) -> bool:
        """Run all validation checks."""
        if not self.config:
            self.print_results()
            return False

        print(f"{Colors.BLUE}🔍 Running production configuration validation...{Colors.END}\n")

        # Run all validation checks
        self.validate_environment_basics()
        self.validate_database_config()
        self.validate_redis_config()
        self.validate_ai_services()
        self.validate_security_config()
        self.validate_ghl_integration()
        self.validate_performance_config()
        self.validate_monitoring_config()
        self.validate_feature_flags()

        # Print results and return status
        return self.print_results()

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Validate Jorge's BI Dashboard production configuration"
    )
    parser.add_argument(
        '--config', '-c',
        default='.env.bi.production',
        help='Path to production configuration file'
    )
    parser.add_argument(
        '--json', '-j',
        action='store_true',
        help='Output results in JSON format'
    )

    args = parser.parse_args()

    validator = ProductionConfigValidator(args.config)

    if args.json:
        # JSON output for automated tools
        results_dict = {
            'status': 'unknown',
            'critical_issues': 0,
            'high_issues': 0,
            'warnings': 0,
            'passes': 0,
            'results': []
        }

        # Run validation silently for JSON mode
        success = validator.run_validation()

        # Convert results to dict format
        for result in validator.results:
            results_dict['results'].append({
                'category': result.category,
                'item': result.item,
                'status': result.status,
                'message': result.message,
                'severity': result.severity
            })

            if result.severity == 'critical':
                results_dict['critical_issues'] += 1
            elif result.severity == 'high':
                results_dict['high_issues'] += 1
            elif result.status == 'warning':
                results_dict['warnings'] += 1
            elif result.status == 'pass':
                results_dict['passes'] += 1

        results_dict['status'] = 'ready' if success else 'not_ready'

        print(json.dumps(results_dict, indent=2))
    else:
        # Standard output
        success = validator.run_validation()

    sys.exit(0 if success else 1)

if __name__ == '__main__':
    main()