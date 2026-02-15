"""
Configuration Validation Tests for Jorge Bots
==============================================

Validates the unified configuration system:
- Config loads successfully
- Value ranges and constraints
- Environment overrides
- Bot-specific settings

Coverage: Config structure, validation rules, environment behavior
"""

import os
import pytest
from ghl_real_estate_ai.config.jorge_config_loader import (
    get_config,
    reload_config,
    JorgeBotsConfig,
)


class TestConfigLoading:
    """Test basic config loading and singleton behavior."""

    def test_config_loads_successfully(self):
        """Config should load without errors."""
        config = get_config()
        assert isinstance(config, JorgeBotsConfig)

    def test_singleton_pattern(self):
        """Multiple calls should return same instance."""
        config1 = get_config()
        config2 = get_config()
        assert config1 is config2

    def test_reload_creates_new_instance(self):
        """reload_config() should refresh the config."""
        config1 = get_config()
        reload_config()
        config2 = get_config()
        # Values should match, but instance refreshed
        assert config1.shared.performance.sla_response_time_seconds == \
               config2.shared.performance.sla_response_time_seconds


class TestConfigValidation:
    """Test config value ranges and constraints."""

    def test_temperature_thresholds_valid_range(self):
        """Temperature thresholds should be 0-100."""
        config = get_config()

        # Lead bot
        assert 0 <= config.lead_bot.temperature_thresholds["hot"] <= 100
        assert 0 <= config.lead_bot.temperature_thresholds["warm"] <= 100
        assert 0 <= config.lead_bot.temperature_thresholds["cold"] <= 100

        # Seller bot
        assert 0 <= config.seller_bot.temperature_thresholds["hot"] <= 100
        assert 0 <= config.seller_bot.temperature_thresholds["warm"] <= 100
        assert 0 <= config.seller_bot.temperature_thresholds["cold"] <= 100

    def test_temperature_thresholds_ordered(self):
        """Hot > Warm > Cold for temperature thresholds."""
        config = get_config()

        # Lead bot
        lead_thresholds = config.lead_bot.temperature_thresholds
        assert lead_thresholds["hot"] > lead_thresholds["warm"]
        assert lead_thresholds["warm"] > lead_thresholds["cold"]

        # Seller bot
        seller_thresholds = config.seller_bot.temperature_thresholds
        assert seller_thresholds["hot"] > seller_thresholds["warm"]
        assert seller_thresholds["warm"] > seller_thresholds["cold"]

    def test_handoff_threshold_valid(self):
        """Handoff confidence threshold should be 0.0-1.0."""
        config = get_config()
        threshold = config.shared.handoff.confidence_threshold
        assert 0.0 <= threshold <= 1.0

    def test_sla_response_time_positive(self):
        """SLA response time should be positive."""
        config = get_config()
        assert config.shared.performance.sla_response_time_seconds > 0

    def test_cache_ttl_positive(self):
        """Cache TTL values should be positive."""
        config = get_config()
        assert config.shared.caching.ttl_lru.ttl_seconds > 0
        for key, ttl in config.shared.caching.ttl_seconds.items():
            assert ttl > 0, f"Invalid TTL for {key}: {ttl}"

    def test_valid_sequence_days_sorted(self):
        """Sequence days should be sorted ascending."""
        config = get_config()
        valid_days = config.lead_bot.sequence.valid_days
        assert valid_days == sorted(valid_days), \
            f"Sequence days not sorted: {valid_days}"

    def test_ab_testing_variants_non_empty(self):
        """A/B testing should have at least one variant."""
        config = get_config()
        variants = config.shared.ab_testing.response_tone.variants
        assert len(variants) > 0, "No A/B testing variants configured"

        # Default should be in variants
        default = config.shared.ab_testing.response_tone.default
        assert default in variants, \
            f"Default variant '{default}' not in variants {variants}"


class TestEnvironmentOverrides:
    """Test environment-specific configuration."""

    def test_development_environment(self, monkeypatch):
        """Development should have relaxed SLA and debug logging."""
        monkeypatch.setenv("DEPLOYMENT_ENV", "development")
        reload_config()
        config = get_config()

        assert config.shared.performance.sla_response_time_seconds == 30
        assert config.shared.observability.log_level == "DEBUG"

    def test_production_environment(self, monkeypatch):
        """Production should have strict SLA and optimizations."""
        monkeypatch.setenv("DEPLOYMENT_ENV", "production")
        reload_config()
        config = get_config()

        assert config.shared.performance.sla_response_time_seconds == 15
        assert config.shared.observability.log_level == "WARNING"
        assert config.shared.caching.enable_l3_disk is True
        assert config.circuit_breaker.enabled is True

        # Production scaling (5x)
        assert config.shared.caching.ttl_lru.max_entries == 5000
        assert config.shared.analytics.temperature_prediction.max_leads_in_memory == 50000

    def test_staging_environment(self, monkeypatch):
        """Staging should have intermediate settings."""
        monkeypatch.setenv("DEPLOYMENT_ENV", "staging")
        reload_config()
        config = get_config()

        assert config.shared.observability.log_level == "INFO"


class TestBotSpecificConfig:
    """Test bot-specific configuration sections."""

    def test_lead_bot_enabled(self):
        """Lead bot should be enabled by default."""
        config = get_config()
        assert config.lead_bot.enabled is True

    def test_buyer_bot_affordability_defaults(self):
        """Buyer bot affordability defaults should be valid."""
        config = get_config()
        afford = config.buyer_bot.affordability

        assert 0.0 < afford.default_dti_ratio <= 1.0, \
            f"Invalid DTI ratio: {afford.default_dti_ratio}"
        assert 0.0 < afford.default_down_payment_percent <= 1.0, \
            f"Invalid down payment: {afford.default_down_payment_percent}"
        assert afford.default_interest_rate > 0.0, \
            f"Invalid interest rate: {afford.default_interest_rate}"

    def test_seller_bot_commission_rate(self):
        """Seller bot commission rate should be valid."""
        config = get_config()
        rate = config.seller_bot.commission_settings["default_rate"]
        assert 0.0 < rate <= 0.20, \
            f"Commission rate {rate} outside valid range (0.0-0.20)"

    def test_frs_pcs_weights_valid(self):
        """FRS and PCS scoring weights should be valid."""
        config = get_config()

        # FRS weights
        frs_weights = config.seller_bot.scoring.frs_weights
        for key, weight in frs_weights.items():
            assert 0.0 <= weight <= 1.0, \
                f"Invalid FRS weight for {key}: {weight}"

        # PCS weights
        pcs_weights = config.seller_bot.scoring.pcs_weights
        for key, weight in pcs_weights.items():
            assert 0.0 <= weight <= 1.0, \
                f"Invalid PCS weight for {key}: {weight}"


class TestCircuitBreakerConfig:
    """Test circuit breaker configuration."""

    def test_circuit_breaker_thresholds_valid(self):
        """Circuit breaker thresholds should be valid."""
        config = get_config()
        cb = config.circuit_breaker

        assert cb.failure_threshold > 0, "Failure threshold must be positive"
        assert cb.recovery_timeout > 0, "Recovery timeout must be positive"
        assert 0.0 <= cb.error_rate_threshold <= 1.0, \
            "Error rate threshold must be 0.0-1.0"

    def test_service_specific_overrides(self):
        """Service-specific circuit breaker settings should override defaults."""
        config = get_config()
        service_settings = config.circuit_breaker.service_overrides

        for service, settings in service_settings.items():
            if "failure_threshold" in settings:
                assert settings["failure_threshold"] > 0
            if "timeout" in settings:
                assert settings["timeout"] > 0


class TestOpenTelemetryConfig:
    """Test OpenTelemetry configuration."""

    def test_otel_sampling_rate_valid(self):
        """OpenTelemetry sampling rate should be 0.0-1.0."""
        config = get_config()
        sampling_rate = config.opentelemetry.sampling_rate
        assert 0.0 <= sampling_rate <= 1.0, \
            f"Invalid sampling rate: {sampling_rate}"

    def test_otel_enabled_in_production(self, monkeypatch):
        """OpenTelemetry should be enabled in production."""
        monkeypatch.setenv("DEPLOYMENT_ENV", "production")
        reload_config()
        config = get_config()

        assert config.opentelemetry.enabled is True
