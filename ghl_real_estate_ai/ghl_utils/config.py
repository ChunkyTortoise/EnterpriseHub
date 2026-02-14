"""
Configuration module for GHL Real Estate AI.

Manages environment variables and application settings using Pydantic.
"""

import os
import sys
from enum import Enum
from typing import Optional

from pydantic import Field, ValidationInfo, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Centralized application settings with environment variable support.

    All sensitive values (API keys, database URLs) are loaded from environment
    variables or .env file. Never hardcode secrets in this file.
    """

    # API Keys (Required)
    anthropic_api_key: str
    ghl_api_key: str  # Default Location API Key
    ghl_location_id: str
    ghl_agency_api_key: Optional[str] = None  # Master Agency Key
    ghl_agency_id: Optional[str] = None

    # LLM Configuration
    claude_model: str = "claude-sonnet-4-5-20250514"
    claude_sonnet_model: str = "claude-sonnet-4-5-20250514"
    claude_haiku_model: str = "claude-sonnet-4-5-20250514"  # Consolidated to Sonnet 4.5
    claude_opus_model: str = "claude-opus-4-5-20251101"  # High-stakes tasks
    temperature: float = 0.7
    max_tokens: int = 150
    default_llm_provider: str = "claude"
    gemini_model: str = Field("gemini-2.0-flash-lite", validation_alias="GEMINI_MODEL")
    google_api_key: Optional[str] = None
    perplexity_api_key: Optional[str] = None
    perplexity_model: str = "sonar"

    # OpenRouter Configuration
    openrouter_api_key: Optional[str] = None
    openrouter_default_model: str = "anthropic/claude-3.5-sonnet"
    openrouter_app_name: str = "EnterpriseHub-Real-Estate-AI"
    openrouter_fallback_models: str = "anthropic/claude-3-sonnet,openai/gpt-4-turbo"
    openrouter_enable_cost_tracking: bool = True

    # LLM Costs (per 1M tokens)
    claude_input_cost_per_1m: float = 3.00
    claude_output_cost_per_1m: float = 15.00
    gemini_input_cost_per_1m: float = 1.25
    gemini_output_cost_per_1m: float = 3.75
    perplexity_input_cost_per_1m: float = 1.00
    perplexity_output_cost_per_1m: float = 1.00
    # OpenRouter costs are dynamic and returned in response headers
    openrouter_input_cost_per_1m: float = 0.0  # Updated from API response
    openrouter_output_cost_per_1m: float = 0.0  # Updated from API response

    # Database Configuration
    database_url: Optional[str] = None  # PostgreSQL (Railway auto-provides)
    redis_url: Optional[str] = None  # Redis for session state

    # Redis Configuration (Real-time Features)
    redis_password: Optional[str] = None
    redis_db: int = 0
    redis_max_connections: int = 20
    redis_socket_timeout: int = 30
    redis_socket_connect_timeout: int = 30
    redis_retry_on_timeout: bool = True
    redis_health_check_interval: int = 30

    # WebSocket Configuration (Real-time Updates)
    websocket_host: str = "localhost"
    websocket_port: int = 8765
    websocket_path: str = "/ws"
    websocket_protocol: str = "ws"
    websocket_secure: bool = False
    websocket_origins: str = "localhost:8501,127.0.0.1:8501"
    websocket_ping_interval: int = 20
    websocket_ping_timeout: int = 10
    websocket_close_timeout: int = 10
    websocket_max_size: int = 1048576  # 1MB
    websocket_max_queue: int = 32
    websocket_reconnect_attempts: int = 5
    websocket_reconnect_delay: int = 2
    websocket_fallback_to_polling: bool = True

    # Real-time Service Configuration
    realtime_enabled: bool = True
    realtime_use_websocket: bool = True
    realtime_poll_interval: int = 2
    realtime_max_events: int = 1000
    realtime_cache_ttl: int = 3600
    realtime_event_dedup_window: int = 30
    realtime_high_priority_threshold: int = 3
    realtime_batch_size: int = 50

    # Vector Database
    chroma_persist_directory: str = "./data/embeddings/chroma_db"
    chroma_collection_name: str = "real_estate_kb"

    # Application Settings
    environment: str = "development"  # development, production
    log_level: str = "INFO"
    app_name: str = "GHL Real Estate AI"
    version: str = "1.0.0"

    # Phase 1-2 Optimizations (Foundation)
    enable_conversation_optimization: bool = False
    enable_enhanced_caching: bool = False
    enable_async_optimization: bool = False

    # Phase 3-4 Advanced Optimizations (80-90% total cost reduction)
    enable_token_budget_enforcement: bool = False
    enable_database_connection_pooling: bool = False
    enable_semantic_response_caching: bool = False
    enable_multi_tenant_optimization: bool = False
    enable_advanced_analytics: bool = False
    enable_cost_prediction: bool = False

    # Optimization Configuration Values
    token_budget_default_monthly: int = 100000
    token_budget_default_daily: int = 5000
    db_pool_size: int = 20
    db_max_overflow: int = 10
    semantic_cache_similarity_threshold: float = 0.85
    semantic_cache_ttl: int = 3600

    # Default Agent Information
    default_agent_name: str = "Sarah Johnson"
    default_agent_phone: str = "+15125551234"
    default_agent_email: str = "agent@example.com"

    # Lead Scoring Thresholds - QUESTION COUNT (Jorge's requirement)
    # Hot: 3+ questions answered, Warm: 2 questions, Cold: 0-1 questions
    hot_lead_threshold: int = 3  # 3+ questions answered
    warm_lead_threshold: int = 2  # 2 questions answered
    cold_lead_threshold: int = 1  # 0-1 questions answered

    # Jorge's Auto-Deactivation Threshold
    # When lead score reaches this percentage, AI deactivates and hands off to human
    auto_deactivate_threshold: int = 70  # 70+ percentage triggers AI deactivation

    # Activation & Trigger Settings
    activation_tags: list[str] = ["Needs Qualifying"]
    deactivation_tags: list[str] = ["AI-Off", "Qualified", "Stop-Bot"]
    required_contact_type: Optional[str] = "Seller"
    disposition_field_name: str = "disposition"
    bot_active_disposition: str = "Needs Qualifying"

    # GHL Workflow & Custom Field Mapping
    notify_agent_workflow_id: Optional[str] = None
    ghl_calendar_id: Optional[str] = None
    jorge_user_id: Optional[str] = None  # Jorge's GHL user ID for appointment assignment
    manual_scheduling_workflow_id: Optional[str] = None  # Workflow for manual scheduling fallback
    custom_field_lead_score: Optional[str] = None
    custom_field_budget: Optional[str] = None
    custom_field_location: Optional[str] = None
    custom_field_timeline: Optional[str] = None
    custom_field_appointment_time: Optional[str] = None  # Store scheduled appointment time
    custom_field_appointment_type: Optional[str] = None  # Store appointment type

    # Phase 2: Custom Field IDs (Seller Bot)
    custom_field_seller_temperature: Optional[str] = None
    custom_field_pcs_score: Optional[str] = None
    custom_field_seller_motivation: Optional[str] = None
    custom_field_timeline_urgency: Optional[str] = None
    custom_field_property_condition: Optional[str] = None
    custom_field_price_expectation: Optional[str] = None
    custom_field_seller_liens: Optional[str] = None
    custom_field_seller_repairs: Optional[str] = None
    custom_field_seller_listing_history: Optional[str] = None
    custom_field_seller_decision_maker: Optional[str] = None

    # Calendar & Appointment Settings (Jorge's Rancho Cucamonga Business)
    appointment_auto_booking_enabled: bool = True
    appointment_booking_threshold: int = 5  # Lead score threshold for auto-booking (70%)
    appointment_buffer_minutes: int = 15  # Buffer time between appointments
    appointment_default_duration: int = 60  # Default appointment duration in minutes
    appointment_max_days_ahead: int = 14  # Maximum days ahead to show availability
    appointment_timezone: str = "America/Los_Angeles"  # Jorge's Rancho Cucamonga timezone

    # Jorge's Business Hours (Pacific Time)
    business_hours_monday_start: str = "09:00"
    business_hours_monday_end: str = "18:00"
    business_hours_tuesday_start: str = "09:00"
    business_hours_tuesday_end: str = "18:00"
    business_hours_wednesday_start: str = "09:00"
    business_hours_wednesday_end: str = "18:00"
    business_hours_thursday_start: str = "09:00"
    business_hours_thursday_end: str = "18:00"
    business_hours_friday_start: str = "09:00"
    business_hours_friday_end: str = "18:00"
    business_hours_saturday_start: str = "10:00"
    business_hours_saturday_end: str = "16:00"
    business_hours_sunday_start: str = "closed"
    business_hours_sunday_end: str = "closed"

    # SMS Confirmation Settings
    sms_confirmation_enabled: bool = True
    sms_confirmation_template: str = "Hi {name}! Your {appointment_type} with Jorge is confirmed for {time}. Jorge will call you to discuss your property goals. Reply RESCHEDULE if needed."

    # Performance Settings
    webhook_timeout_seconds: int = 3
    max_conversation_history_length: int = 20
    previous_context_window_hours: int = 24
    rag_top_k_results: int = 3

    # Twilio Configuration
    twilio_account_sid: str = "your_twilio_account_sid"
    twilio_auth_token: str = "your_twilio_auth_token"
    twilio_phone_number: str = "+15125551234"
    webhook_base_url: str = "http://localhost:8000"

    # SendGrid Configuration
    sendgrid_api_key: str = "your_sendgrid_api_key"
    sendgrid_sender_email: str = "agent@example.com"
    sendgrid_sender_name: str = "GHL AI Assistant"

    # Security
    ghl_webhook_secret: Optional[str] = None  # For signature verification
    # SECURITY: JWT secret must be provided via environment variable.
    # No default value to prevent accidental use of weak secrets in production.
    # In development, set JWT_SECRET_KEY in .env file.
    jwt_secret_key: Optional[str] = Field(default=None)
    apollo_webhook_secret: Optional[str] = None
    twilio_webhook_secret: Optional[str] = None
    sendgrid_webhook_secret: Optional[str] = None

    # Vapi.ai Configuration
    vapi_api_key: Optional[str] = None
    vapi_assistant_id: Optional[str] = None
    vapi_phone_number_id: Optional[str] = None
    vapi_webhook_secret: Optional[str] = None

    # Retell AI Configuration (Added for Phase 2)
    retell_api_key: Optional[str] = None
    retell_agent_id: Optional[str] = None
    retell_webhook_secret: Optional[str] = None

    # Testing
    test_mode: bool = False

    @field_validator("jwt_secret_key")
    @classmethod
    def validate_jwt_secret(cls, v: Optional[str], info: ValidationInfo):
        """
        SECURITY FIX: Validate JWT secret with fail-fast pattern.

        - Production: MUST have 32+ character secret, exits immediately if missing/weak
        - Development: Generates a temporary secret with warning, but logs it clearly
        """
        import logging
        import secrets as secrets_module

        environment = info.data.get("environment", "development")

        # Production: Fail fast if no secret or weak secret
        if environment == "production":
            if not v:
                print("=" * 60)
                print("CRITICAL SECURITY ERROR: JWT_SECRET_KEY is required in production")
                print("=" * 60)
                print("The application cannot start without a secure JWT secret.")
                print("")
                print("To fix this:")
                print("  1. Generate a secure secret:")
                print("     openssl rand -hex 32")
                print("  2. Set the environment variable:")
                print("     export JWT_SECRET_KEY='your-generated-secret'")
                print("=" * 60)
                sys.exit(1)
            if len(v) < 32:
                print("=" * 60)
                print("CRITICAL SECURITY ERROR: JWT_SECRET_KEY is too weak")
                print("=" * 60)
                print(f"Current length: {len(v)} characters (minimum: 32)")
                print("")
                print("Generate a secure secret with:")
                print("  openssl rand -hex 32")
                print("=" * 60)
                sys.exit(1)
            return v

        # Development: Allow missing secret but generate temporary one with clear warning
        if not v:
            temp_secret = secrets_module.token_urlsafe(32)
            logging.warning(
                "JWT_SECRET_KEY not set - using temporary secret for development. "
                "This secret will change on restart. Set JWT_SECRET_KEY in .env for persistence."
            )
            return temp_secret

        # Development with provided secret: warn if weak
        if len(v) < 32:
            logging.warning(
                f"JWT_SECRET_KEY is only {len(v)} characters. "
                "For security, use at least 32 characters (openssl rand -hex 32)"
            )

        return v

    @field_validator("ghl_webhook_secret")
    @classmethod
    def validate_webhook_secret(cls, v: Optional[str], info: ValidationInfo):
        """SECURITY FIX: Validate webhook secret in production."""
        environment = info.data.get("environment", "development")
        if environment == "production" and not v:
            print("❌ SECURITY ERROR: GHL_WEBHOOK_SECRET is required in production")
            print("   Generate with: openssl rand -hex 32")
            sys.exit(1)
        if v and len(v) < 32:
            print("⚠️  WARNING: Webhook secret should be at least 32 characters")
        return v

    @field_validator("redis_password")
    @classmethod
    def validate_redis_password(cls, v: Optional[str], info: ValidationInfo):
        """SECURITY FIX: Validate Redis password in production."""
        environment = info.data.get("environment", "development")
        if environment == "production" and not v:
            print("❌ SECURITY ERROR: REDIS_PASSWORD is required in production")
            print("   Generate with: openssl rand -hex 32")
            sys.exit(1)
        if v and len(v) < 32:
            print("⚠️  WARNING: Redis password should be at least 32 characters")
        return v

    @field_validator("anthropic_api_key")
    @classmethod
    def validate_anthropic_key(cls, v: str):
        """Validate Anthropic API key format."""
        if v and not v.startswith("sk-ant-"):
            print("⚠️  WARNING: Anthropic API key should start with 'sk-ant-'")
        return v

    @field_validator("ghl_api_key")
    @classmethod
    def validate_ghl_key(cls, v: str):
        """Validate GHL API key format."""
        if v and not v.startswith("eyJ"):
            print("⚠️  WARNING: GHL API key should be JWT format (starts with 'eyJ')")
        return v

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore", case_sensitive=False)


# Global settings instance
# This will be imported throughout the application
try:
    settings = Settings()
except Exception as e:
    # Provide a clear, actionable error instead of a raw Pydantic traceback
    missing = [var for var in ("ANTHROPIC_API_KEY", "GHL_API_KEY", "GHL_LOCATION_ID") if not os.getenv(var)]
    if missing:
        print(f"\n❌  STARTUP ERROR: Required environment variables not set: {', '.join(missing)}")
        print("   Copy .env.example → .env and fill in the values, or set them in your Railway dashboard.\n")
    else:
        print(f"\n❌  STARTUP ERROR: Configuration validation failed: {e}\n")
    raise SystemExit(1)


# Environment Mode Detection
class EnvironmentMode(Enum):
    """Application environment modes"""

    DEMO = "demo"  # Mock data, no API calls (default)
    STAGING = "staging"  # Real API, test account
    PRODUCTION = "production"  # Real API, production account


def get_environment() -> EnvironmentMode:
    """
    Detect environment based on GHL_API_KEY and ENVIRONMENT variable

    Returns:
        EnvironmentMode: Current environment (DEMO, STAGING, or PRODUCTION)
    """
    env_var = os.getenv("ENVIRONMENT", "").lower()
    api_key = os.getenv("GHL_API_KEY", "")

    # Explicit environment variable takes precedence
    if env_var == "production":
        return EnvironmentMode.PRODUCTION
    elif env_var == "staging":
        return EnvironmentMode.STAGING
    elif env_var == "demo":
        return EnvironmentMode.DEMO

    # Auto-detect based on API key
    if not api_key or api_key == "demo_mode" or api_key == "dummy":
        return EnvironmentMode.DEMO
    elif api_key.startswith("test_") or "test" in api_key.lower():
        return EnvironmentMode.STAGING
    else:
        return EnvironmentMode.PRODUCTION


def is_mock_mode() -> bool:
    """
    Check if application should use mock data

    Returns:
        bool: True if in DEMO mode, False otherwise
    """
    return get_environment() == EnvironmentMode.DEMO


def get_environment_display() -> dict:
    """
    Get environment display information for UI

    Returns:
        dict: Environment info with icon, color, and message
    """
    env = get_environment()

    if env == EnvironmentMode.DEMO:
        return {
            "icon": "🎭",
            "name": "Demo Mode",
            "color": "#F59E0B",
            "message": "Using sample data. Set GHL_API_KEY to enable live sync.",
            "banner_type": "info",
        }
    elif env == EnvironmentMode.STAGING:
        return {
            "icon": "🧪",
            "name": "Staging Mode",
            "color": "#3B82F6",
            "message": "Connected to test environment.",
            "banner_type": "info",
        }
    else:  # PRODUCTION
        return {
            "icon": "✅",
            "name": "Live Mode",
            "color": "#10B981",
            "message": "Connected to GoHighLevel production.",
            "banner_type": "success",
        }
