"""
Component Migration Framework
=============================

Automated migration tooling for EnterpriseHub Streamlit components.

Provides:
- Component analysis and scoring
- Automated migration to enterprise standards
- Theme unification
- Claude AI integration templates
- Validation and testing
- Rollback capabilities

Author: EnterpriseHub Development Team
Date: January 2026
Version: 1.0.0
"""

from .component_analyzer import ComponentAnalyzer, ComponentAnalysis, MigrationStatus
from .migration_engine import MigrationEngine, MigrationConfig, MigrationResult
from .theme_migrator import ThemeMigrator
from .claude_integration_templates import ClaudeIntegrationTemplates
from .validation_suite import ValidationSuite, ValidationResult

__all__ = [
    'ComponentAnalyzer',
    'ComponentAnalysis',
    'MigrationStatus',
    'MigrationEngine',
    'MigrationConfig',
    'MigrationResult',
    'ThemeMigrator',
    'ClaudeIntegrationTemplates',
    'ValidationSuite',
    'ValidationResult'
]
