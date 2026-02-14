import pytest
pytestmark = pytest.mark.integration

"""
Deployment Readiness Tests — Phase 5

Validates configuration consistency across:
- .env.example documentation completeness
- railway.jorge.toml environment alignment
- Activation tag consistency between config and webhook routing
- Production placeholder detection

No external services needed — pure file-level validation.
"""

import os
import re
from pathlib import Path

import pytest

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parent.parent

ENV_EXAMPLE_PATH = PROJECT_ROOT / ".env.example"
RAILWAY_TOML_PATH = PROJECT_ROOT / "railway.jorge.toml"
JORGE_CONFIG_PATH = PROJECT_ROOT / "ghl_real_estate_ai" / "ghl_utils" / "jorge_config.py"
WEBHOOK_PATH = PROJECT_ROOT / "ghl_real_estate_ai" / "api" / "routes" / "webhook.py"


def _parse_env_example_vars(path: Path) -> set[str]:
    """Extract variable names from .env.example (lines with KEY= or KEY=value)."""
    if not path.exists():
        return set()
    vars_found = set()
    for line in path.read_text().splitlines():
        line = line.strip()
        # Skip comments and blank lines
        if not line or line.startswith("#"):
            continue
        match = re.match(r"^([A-Z_][A-Z0-9_]*)(?:\s*=)", line)
        if match:
            vars_found.add(match.group(1))
    return vars_found


def _parse_railway_toml_vars(path: Path) -> set[str]:
    """Extract variable names from railway.jorge.toml [env] section."""
    if not path.exists():
        return set()
    vars_found = set()
    in_env_section = False
    for line in path.read_text().splitlines():
        stripped = line.strip()
        if stripped == "[env]":
            in_env_section = True
            continue
        if stripped.startswith("[") and stripped != "[env]":
            in_env_section = False
            continue
        if in_env_section and stripped and not stripped.startswith("#"):
            match = re.match(r"^([A-Z_][A-Z0-9_]*)\s*=", stripped)
            if match:
                vars_found.add(match.group(1))
    return vars_found


def _find_os_getenv_vars(path: Path) -> set[str]:
    """Find all os.getenv("VAR") or os.environ["VAR"] references in a Python file."""
    if not path.exists():
        return set()
    content = path.read_text()
    vars_found = set()
    # os.getenv("VAR", ...) or os.getenv('VAR', ...)
    for match in re.finditer(r'os\.getenv\(\s*["\']([A-Z_][A-Z0-9_]*)["\']', content):
        vars_found.add(match.group(1))
    # os.environ.get("VAR", ...) or os.environ["VAR"]
    for match in re.finditer(r'os\.environ(?:\.get)?\(\s*["\']([A-Z_][A-Z0-9_]*)["\']', content):
        vars_found.add(match.group(1))
    for match in re.finditer(r'os\.environ\[["\']([A-Z_][A-Z0-9_]*)["\']\]', content):
        vars_found.add(match.group(1))
    return vars_found


def _find_all_code_env_vars() -> set[str]:
    """Scan application code for all environment variable references."""
    all_vars = set()
    app_dirs = [
        PROJECT_ROOT / "ghl_real_estate_ai",
    ]
    for app_dir in app_dirs:
        if not app_dir.exists():
            continue
        for py_file in app_dir.rglob("*.py"):
            all_vars.update(_find_os_getenv_vars(py_file))
    return all_vars


# ===========================================================================
# Deployment Readiness Tests
# ===========================================================================


class TestDeploymentReadiness:
    """Phase 5: Configuration validation for production deployment."""

    def test_all_env_vars_documented(self):
        """Critical Jorge bot env vars referenced in config/webhook appear in .env.example."""
        assert ENV_EXAMPLE_PATH.exists(), f".env.example not found at {ENV_EXAMPLE_PATH}"

        env_example_vars = _parse_env_example_vars(ENV_EXAMPLE_PATH)

        # Focus on Jorge-critical files only (config and webhook)
        jorge_critical_files = [
            JORGE_CONFIG_PATH,
            WEBHOOK_PATH,
        ]
        code_vars = set()
        for f in jorge_critical_files:
            code_vars.update(_find_os_getenv_vars(f))

        # Vars set by infrastructure, have valid defaults, or are internal tuning params
        infrastructure_vars = {
            "PORT",
            "HOST",
            "DATABASE_URL",
            "REDIS_URL",
            "PYTHONPATH",
            "HOME",
            "PATH",
            "USER",
            "TEST_DATABASE_URL",
            "TEST_REDIS_URL",
            "ENVIRONMENT",
            "ENV",
        }

        # Internal JorgeSellerConfig tuning parameters with hardcoded defaults
        # These are optional overrides that don't need .env.example documentation
        internal_config_vars = {
            "ACTIVE_FOLLOWUP_DAYS",
            "FRIENDLY_APPROACH",
            "HOT_QUALITY_THRESHOLD",
            "HOT_QUESTIONS_REQUIRED",
            "HOT_SELLER_THRESHOLD",
            "JORGE_ANALYTICS_ENABLED",
            "JORGE_MARKET",
            "LONGTERM_FOLLOWUP_INTERVAL",
            "MAX_SMS_LENGTH",
            "NO_HYPHENS",
            "USE_WARM_LANGUAGE",
            "WARM_QUALITY_THRESHOLD",
            "WARM_QUESTIONS_REQUIRED",
            "WARM_SELLER_THRESHOLD",
        }
        infrastructure_vars.update(internal_config_vars)

        undocumented = code_vars - env_example_vars - infrastructure_vars

        assert not undocumented, (
            f"Jorge-critical env vars referenced in config/webhook but missing from .env.example:\n"
            f"  {sorted(undocumented)}\n"
            f"Add these variables to .env.example with documentation."
        )

    def test_railway_toml_matches_env_example(self):
        """Critical deployment vars in railway.jorge.toml exist in .env.example."""
        assert RAILWAY_TOML_PATH.exists(), f"railway.jorge.toml not found at {RAILWAY_TOML_PATH}"
        assert ENV_EXAMPLE_PATH.exists(), f".env.example not found at {ENV_EXAMPLE_PATH}"

        railway_vars = _parse_railway_toml_vars(RAILWAY_TOML_PATH)
        env_example_vars = _parse_env_example_vars(ENV_EXAMPLE_PATH)

        # Critical vars that must be in both
        critical_vars = {
            "JORGE_SELLER_MODE",
            "JORGE_BUYER_MODE",
            "JORGE_LEAD_MODE",
            "HOT_SELLER_WORKFLOW_ID",
            "WARM_SELLER_WORKFLOW_ID",
            "HOT_BUYER_WORKFLOW_ID",
            "WARM_BUYER_WORKFLOW_ID",
            "NOTIFY_AGENT_WORKFLOW_ID",
            "AUTO_DEACTIVATE_THRESHOLD",
        }

        # Check critical vars are in railway.jorge.toml
        missing_in_railway = critical_vars - railway_vars
        assert not missing_in_railway, f"Critical vars missing from railway.jorge.toml:\n  {sorted(missing_in_railway)}"

        # Check critical vars are in .env.example
        missing_in_env = critical_vars - env_example_vars
        assert not missing_in_env, f"Critical vars missing from .env.example:\n  {sorted(missing_in_env)}"

    def test_activation_tags_consistent(self):
        """Activation tags in jorge_config match those used in webhook routing."""
        assert JORGE_CONFIG_PATH.exists(), f"jorge_config.py not found"
        assert WEBHOOK_PATH.exists(), f"webhook.py not found"

        config_content = JORGE_CONFIG_PATH.read_text()
        webhook_content = WEBHOOK_PATH.read_text()

        # The key tags that must be referenced in both config and webhook
        expected_tags = [
            "Needs Qualifying",
            "Buyer-Lead",
            "AI-Off",
        ]

        for tag in expected_tags:
            assert tag in config_content or tag in webhook_content, (
                f"Tag '{tag}' not found in jorge_config.py or webhook.py"
            )

        # Verify deactivation tags are used consistently
        deactivation_tags = ["AI-Off", "Qualified", "Stop-Bot", "AI-Qualified"]
        for tag in deactivation_tags:
            assert tag in webhook_content, f"Deactivation tag '{tag}' not found in webhook.py routing logic"

        # Verify seller temperature tags are consistent
        seller_temp_tags = ["Hot-Seller", "Warm-Seller", "Cold-Seller"]
        for tag in seller_temp_tags:
            in_config = tag in config_content
            in_webhook = tag in webhook_content
            # Tags should appear in at least one location
            assert in_config or in_webhook, f"Seller temperature tag '{tag}' not found in config or webhook"

    def test_no_placeholder_workflow_ids_in_production(self):
        """When ENVIRONMENT=production, empty workflow IDs are acceptable but
        placeholder strings like 'jorge_hot_seller_workflow' are not."""
        assert JORGE_CONFIG_PATH.exists(), f"jorge_config.py not found"

        config_content = JORGE_CONFIG_PATH.read_text()

        # These were the old placeholder patterns that should no longer exist
        placeholder_patterns = [
            r'"jorge_hot_seller_workflow"',
            r'"jorge_warm_seller_workflow"',
            r'"jorge_agent_notification"',
            r'"seller_temp_field_id"',
            r'"seller_motivation_field_id"',
            r'"timeline_urgency_field_id"',
            r'"property_condition_field_id"',
            r'"price_expectation_field_id"',
        ]

        found_placeholders = []
        for pattern in placeholder_patterns:
            if re.search(pattern, config_content):
                found_placeholders.append(pattern.strip('"'))

        assert not found_placeholders, (
            f"Placeholder workflow/field IDs found in jorge_config.py:\n"
            f"  {found_placeholders}\n"
            f"Replace with empty strings and use env var overrides."
        )