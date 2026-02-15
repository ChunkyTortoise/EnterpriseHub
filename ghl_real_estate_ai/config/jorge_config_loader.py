"""
Unified Configuration Loader for Jorge Bots

Loads centralized configuration from jorge_bots.yaml and provides typed access.
Supports environment-specific overrides and runtime config updates.

Usage:
    from ghl_real_estate_ai.config.jorge_config_loader import get_config
    
    config = get_config()
    if config.lead_bot.features.enable_predictive_analytics:
        # Enable predictive features
    
    # Or get bot-specific config
    lead_config = get_config().lead_bot
    sla = get_config().shared.performance.sla_response_time_seconds
"""
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

import yaml

from ghl_real_estate_ai.ghl_utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class PerformanceConfig:
    sla_response_time_seconds: int = 15
    max_concurrent_tasks: int = 5
    cost_per_token: float = 0.000015
    enable_response_streaming: bool = True


@dataclass
class TTLLRUCacheConfig:
    """Configuration for TTL-based LRU cache (Task #15 extraction)"""
    max_entries: int = 1000
    ttl_seconds: int = 3600


@dataclass
class CachingConfig:
    enable_l1_redis: bool = True
    enable_l2_memory: bool = True
    enable_l3_disk: bool = False
    ttl_lru: TTLLRUCacheConfig = field(default_factory=TTLLRUCacheConfig)
    ttl_seconds: Dict[str, int] = field(default_factory=dict)


@dataclass
class ObservabilityConfig:
    enable_opentelemetry: bool = False
    enable_performance_tracking: bool = True
    enable_metrics_collection: bool = True
    log_level: str = "INFO"
    log_format: str = "json"


@dataclass
class IntegrationsConfig:
    enable_ghl: bool = True
    ghl_rate_limit_per_second: int = 10
    enable_retell: bool = True
    enable_sendgrid: bool = True
    enable_lyrio: bool = True
    enable_stripe: bool = False


@dataclass
class EarlyDetectionConfig:
    """Configuration for handoff early detection (Task #19)"""
    enabled: bool = True
    threshold: float = 0.7
    log_all_signals: bool = True
    performance_mode: str = "fast"


@dataclass
class HandoffConfig:
    enable_jorge_handoff: bool = True
    confidence_threshold: float = 0.7
    circular_prevention_window_minutes: int = 30
    rate_limits: Dict[str, int] = field(default_factory=dict)
    enable_pattern_learning: bool = True
    min_data_points_for_adjustment: int = 10
    early_detection: EarlyDetectionConfig = field(default_factory=EarlyDetectionConfig)


@dataclass
class BehavioralEngineConfig:
    """Configuration for Behavioral Analytics Engine (Task #15 extraction)"""
    cache_max_entries: int = 1000
    cache_ttl_seconds: int = 3600
    pattern_min_samples: int = 5


@dataclass
class TemperaturePredictionConfig:
    """Configuration for Temperature Prediction Engine (Task #15 extraction)"""
    max_leads_in_memory: int = 10000
    prediction_window_days: int = 30
    model_refresh_hours: int = 24


@dataclass
class AnalyticsConfig:
    """Configuration for analytics engines"""
    behavioral_engine: BehavioralEngineConfig = field(default_factory=BehavioralEngineConfig)
    temperature_prediction: TemperaturePredictionConfig = field(default_factory=TemperaturePredictionConfig)


@dataclass
class ResponseToneConfig:
    """Configuration for A/B testing response tone (Task #22)"""
    experiment_name: str = "response_tone_v1"
    variants: List[str] = field(default_factory=lambda: ["formal", "casual", "empathetic"])
    default: str = "empathetic"
    assignment_strategy: str = "deterministic"


@dataclass
class ABTestingConfig:
    """Configuration for A/B testing experiments"""
    enabled: bool = True
    response_tone: ResponseToneConfig = field(default_factory=ResponseToneConfig)


@dataclass
class SharedConfig:
    performance: PerformanceConfig = field(default_factory=PerformanceConfig)
    caching: CachingConfig = field(default_factory=CachingConfig)
    observability: ObservabilityConfig = field(default_factory=ObservabilityConfig)
    integrations: IntegrationsConfig = field(default_factory=IntegrationsConfig)
    handoff: HandoffConfig = field(default_factory=HandoffConfig)
    analytics: AnalyticsConfig = field(default_factory=AnalyticsConfig)
    ab_testing: ABTestingConfig = field(default_factory=ABTestingConfig)


@dataclass
class LeadBotFeatures:
    enable_predictive_analytics: bool = False
    enable_behavioral_optimization: bool = False
    enable_personality_adaptation: bool = False
    enable_track3_intelligence: bool = False
    enable_bot_intelligence: bool = False


@dataclass
class LeadBotWorkflow:
    default_sequence_timing: bool = True
    sequence_days: List[int] = field(default_factory=lambda: [3, 7, 14, 30])
    personality_detection_enabled: bool = True


@dataclass
class LeadBotScoring:
    frs_weights: Dict[str, float] = field(default_factory=dict)


@dataclass
class LeadBotSequence:
    """Configuration for sequence day mapping (Task #23)"""
    default_initial_day: str = "day_3"
    valid_days: List[int] = field(default_factory=lambda: [0, 3, 7, 14, 30])
    boundary_handling: str = "round_down"
    invalid_fallback: str = "day_3"


@dataclass
class LeadBotConfig:
    enabled: bool = True
    features: LeadBotFeatures = field(default_factory=LeadBotFeatures)
    workflow: LeadBotWorkflow = field(default_factory=LeadBotWorkflow)
    scoring: LeadBotScoring = field(default_factory=LeadBotScoring)
    sequence: LeadBotSequence = field(default_factory=LeadBotSequence)
    temperature_thresholds: Dict[str, int] = field(default_factory=dict)
    follow_up: Dict[str, any] = field(default_factory=dict)


@dataclass
class BuyerBotFeatures:
    enable_bot_intelligence: bool = False
    enable_handoff: bool = True
    enable_persona_classification: bool = True
    enable_conversation_memory: bool = False


@dataclass
class BuyerBotWorkflow:
    enable_financial_readiness: bool = True
    enable_affordability_calc: bool = True
    enable_property_matching: bool = True
    enable_objection_handling: bool = True


@dataclass
class BuyerBotAffordability:
    default_dti_ratio: float = 0.43
    default_down_payment_percent: float = 0.20
    default_interest_rate: float = 0.065
    pmi_threshold: float = 0.20


@dataclass
class BuyerBotMemory:
    enable_redis_persistence: bool = False
    conversation_window_size: int = 5
    ttl_days: int = 30


@dataclass
class BuyerBotConfig:
    enabled: bool = True
    features: BuyerBotFeatures = field(default_factory=BuyerBotFeatures)
    workflow: BuyerBotWorkflow = field(default_factory=BuyerBotWorkflow)
    affordability: BuyerBotAffordability = field(default_factory=BuyerBotAffordability)
    personas: List[str] = field(default_factory=list)
    objection_types: List[str] = field(default_factory=list)
    memory: BuyerBotMemory = field(default_factory=BuyerBotMemory)


@dataclass
class SellerBotFeatures:
    enable_progressive_skills: bool = False
    enable_agent_mesh: bool = False
    enable_mcp_integration: bool = False
    enable_adaptive_questioning: bool = False
    enable_track3_intelligence: bool = True
    enable_bot_intelligence: bool = True
    enable_adaptive_negotiation: bool = False


@dataclass
class SellerBotWorkflow:
    enable_cma_generation: bool = True
    enable_pricing_guidance: bool = True
    enable_market_analysis: bool = True
    enable_objection_handling: bool = True
    enable_stall_detection: bool = True


@dataclass
class SellerBotScoring:
    frs_weights: Dict[str, float] = field(default_factory=dict)
    pcs_weights: Dict[str, float] = field(default_factory=dict)


@dataclass
class SellerBotConfig:
    enabled: bool = True
    features: SellerBotFeatures = field(default_factory=SellerBotFeatures)
    workflow: SellerBotWorkflow = field(default_factory=SellerBotWorkflow)
    scoring: SellerBotScoring = field(default_factory=SellerBotScoring)
    temperature_thresholds: Dict[str, int] = field(default_factory=dict)
    commission_settings: Dict[str, any] = field(default_factory=dict)
    objection_categories: List[str] = field(default_factory=list)
    follow_up: Dict[str, any] = field(default_factory=dict)


@dataclass
class CircuitBreakerDefaults:
    failure_threshold: int = 5
    success_threshold: int = 3
    timeout_seconds: int = 60
    half_open_max_calls: int = 2


@dataclass
class CircuitBreakerConfig:
    enabled: bool = False
    defaults: CircuitBreakerDefaults = field(default_factory=CircuitBreakerDefaults)
    services: Dict[str, Dict[str, int]] = field(default_factory=dict)


@dataclass
class OpenTelemetryConfig:
    enabled: bool = False
    exporter: Dict[str, str] = field(default_factory=dict)
    sampling: Dict[str, float] = field(default_factory=dict)
    resource_attributes: Dict[str, str] = field(default_factory=dict)
    spans: Dict[str, bool] = field(default_factory=dict)


@dataclass
class JorgeBotsConfig:
    """Root configuration for all Jorge bots"""
    shared: SharedConfig = field(default_factory=SharedConfig)
    lead_bot: LeadBotConfig = field(default_factory=LeadBotConfig)
    buyer_bot: BuyerBotConfig = field(default_factory=BuyerBotConfig)
    seller_bot: SellerBotConfig = field(default_factory=SellerBotConfig)
    circuit_breaker: CircuitBreakerConfig = field(default_factory=CircuitBreakerConfig)
    opentelemetry: OpenTelemetryConfig = field(default_factory=OpenTelemetryConfig)
    environments: Dict[str, Dict] = field(default_factory=dict)


class JorgeConfigLoader:
    """Loads and manages Jorge bots configuration"""

    _instance: Optional["JorgeConfigLoader"] = None
    _config: Optional[JorgeBotsConfig] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if self._config is None:
            self._load_config()

    def _load_config(self) -> None:
        """Load configuration from YAML file"""
        config_path = Path(__file__).parent / "jorge_bots.yaml"
        
        if not config_path.exists():
            logger.warning(f"Config file not found: {config_path}, using defaults")
            self._config = JorgeBotsConfig()
            return

        with open(config_path) as f:
            raw_config = yaml.safe_load(f)

        # Apply environment-specific overrides
        env = os.getenv("DEPLOYMENT_ENV", "development")
        if env in raw_config.get("environments", {}):
            env_overrides = raw_config["environments"][env]
            self._merge_config(raw_config, env_overrides)

        self._config = self._parse_config(raw_config)
        logger.info(f"Loaded Jorge bots config from {config_path} (env: {env})")

    def _merge_config(self, base: Dict, override: Dict) -> None:
        """Recursively merge override config into base config"""
        for key, value in override.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                self._merge_config(base[key], value)
            else:
                base[key] = value

    def _parse_config(self, raw: Dict) -> JorgeBotsConfig:
        """Parse raw YAML into typed config objects"""
        shared_data = raw.get("shared", {})

        # Parse caching with TTL LRU support
        caching_data = shared_data.get("caching", {})
        caching = CachingConfig(
            enable_l1_redis=caching_data.get("enable_l1_redis", True),
            enable_l2_memory=caching_data.get("enable_l2_memory", True),
            enable_l3_disk=caching_data.get("enable_l3_disk", False),
            ttl_lru=TTLLRUCacheConfig(**caching_data.get("ttl_lru", {})),
            ttl_seconds=caching_data.get("ttl_seconds", {}),
        )

        # Parse analytics with behavioral and temperature prediction engines
        analytics_data = shared_data.get("analytics", {})
        analytics = AnalyticsConfig(
            behavioral_engine=BehavioralEngineConfig(**analytics_data.get("behavioral_engine", {})),
            temperature_prediction=TemperaturePredictionConfig(**analytics_data.get("temperature_prediction", {})),
        )

        # Parse handoff with early detection (Task #19)
        handoff_data = shared_data.get("handoff", {})
        early_detection = EarlyDetectionConfig(**handoff_data.get("early_detection", {}))
        handoff = HandoffConfig(
            enable_jorge_handoff=handoff_data.get("enable_jorge_handoff", True),
            confidence_threshold=handoff_data.get("confidence_threshold", 0.7),
            circular_prevention_window_minutes=handoff_data.get("circular_prevention_window_minutes", 30),
            rate_limits=handoff_data.get("rate_limits", {}),
            enable_pattern_learning=handoff_data.get("enable_pattern_learning", True),
            min_data_points_for_adjustment=handoff_data.get("min_data_points_for_adjustment", 10),
            early_detection=early_detection,
        )

        # Parse A/B testing (Task #22)
        ab_testing_data = shared_data.get("ab_testing", {})
        ab_testing = ABTestingConfig(
            enabled=ab_testing_data.get("enabled", True),
            response_tone=ResponseToneConfig(**ab_testing_data.get("response_tone", {})),
        )

        shared = SharedConfig(
            performance=PerformanceConfig(**shared_data.get("performance", {})),
            caching=caching,
            observability=ObservabilityConfig(**shared_data.get("observability", {})),
            integrations=IntegrationsConfig(**shared_data.get("integrations", {})),
            handoff=handoff,
            analytics=analytics,
            ab_testing=ab_testing,
        )

        lead_data = raw.get("lead_bot", {})
        lead_bot = LeadBotConfig(
            enabled=lead_data.get("enabled", True),
            features=LeadBotFeatures(**lead_data.get("features", {})),
            workflow=LeadBotWorkflow(**lead_data.get("workflow", {})),
            scoring=LeadBotScoring(**lead_data.get("scoring", {})),
            sequence=LeadBotSequence(**lead_data.get("sequence", {})),
            temperature_thresholds=lead_data.get("temperature_thresholds", {}),
            follow_up=lead_data.get("follow_up", {}),
        )

        buyer_data = raw.get("buyer_bot", {})
        buyer_bot = BuyerBotConfig(
            enabled=buyer_data.get("enabled", True),
            features=BuyerBotFeatures(**buyer_data.get("features", {})),
            workflow=BuyerBotWorkflow(**buyer_data.get("workflow", {})),
            affordability=BuyerBotAffordability(**buyer_data.get("affordability", {})),
            personas=buyer_data.get("personas", []),
            objection_types=buyer_data.get("objection_types", []),
            memory=BuyerBotMemory(**buyer_data.get("memory", {})),
        )

        seller_data = raw.get("seller_bot", {})
        seller_bot = SellerBotConfig(
            enabled=seller_data.get("enabled", True),
            features=SellerBotFeatures(**seller_data.get("features", {})),
            workflow=SellerBotWorkflow(**seller_data.get("workflow", {})),
            scoring=SellerBotScoring(**seller_data.get("scoring", {})),
            temperature_thresholds=seller_data.get("temperature_thresholds", {}),
            commission_settings=seller_data.get("commission_settings", {}),
            objection_categories=seller_data.get("objection_categories", []),
            follow_up=seller_data.get("follow_up", {}),
        )

        cb_data = raw.get("circuit_breaker", {})
        circuit_breaker = CircuitBreakerConfig(
            enabled=cb_data.get("enabled", False),
            defaults=CircuitBreakerDefaults(**cb_data.get("defaults", {})),
            services=cb_data.get("services", {}),
        )

        otel_data = raw.get("opentelemetry", {})
        opentelemetry = OpenTelemetryConfig(**otel_data)

        return JorgeBotsConfig(
            shared=shared,
            lead_bot=lead_bot,
            buyer_bot=buyer_bot,
            seller_bot=seller_bot,
            circuit_breaker=circuit_breaker,
            opentelemetry=opentelemetry,
            environments=raw.get("environments", {}),
        )

    def get_config(self) -> JorgeBotsConfig:
        """Get the current configuration"""
        if self._config is None:
            self._load_config()
        return self._config

    def reload(self) -> None:
        """Reload configuration from disk"""
        self._config = None
        self._load_config()


# Global singleton instance
_loader = JorgeConfigLoader()


def get_config() -> JorgeBotsConfig:
    """Get the global Jorge bots configuration"""
    return _loader.get_config()


def reload_config() -> None:
    """Reload configuration from disk"""
    _loader.reload()
