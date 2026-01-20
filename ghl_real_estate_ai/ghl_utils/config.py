"""
Configuration module for GHL Real Estate AI.

Manages environment variables and application settings using Pydantic.
"""
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, validator
from typing import Optional
from enum import Enum
import os
import sys


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
    claude_model: str = "claude-3-5-sonnet-20240620"
    claude_sonnet_model: str = "claude-3-5-sonnet-20240620"
    claude_haiku_model: str = "claude-3-haiku-20240307"
    temperature: float = 0.7
    max_tokens: int = 150
    default_llm_provider: str = "claude"
    gemini_model: str = "gemini-1.5-pro-latest"
    google_api_key: Optional[str] = None
    perplexity_api_key: Optional[str] = None
    perplexity_model: str = "sonar"

    # LLM Costs (per 1M tokens)
    claude_input_cost_per_1m: float = 3.00
    claude_output_cost_per_1m: float = 15.00
    gemini_input_cost_per_1m: float = 1.25
    gemini_output_cost_per_1m: float = 3.75
    perplexity_input_cost_per_1m: float = 1.00
    perplexity_output_cost_per_1m: float = 1.00

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
    activation_tags: list[str] = ["Hit List", "Need to Qualify", "Needs Qualifying"]
    deactivation_tags: list[str] = ["AI-Off", "Qualified", "Stop-Bot"]
    required_contact_type: Optional[str] = "Seller"
    disposition_field_name: str = "disposition"
    bot_active_disposition: str = "Hit List"

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

    # Security
    ghl_webhook_secret: Optional[str] = None  # For signature verification
    jwt_secret_key: str = Field(default="development-jwt-secret-key-for-testing-only-not-for-production-use")  # JWT signing secret
    apollo_webhook_secret: Optional[str] = None
    twilio_webhook_secret: Optional[str] = None
    sendgrid_webhook_secret: Optional[str] = None

    # Testing
    test_mode: bool = False

    @validator('jwt_secret_key')
    def validate_jwt_secret(cls, v, values):
        """SECURITY FIX: Validate JWT secret in production."""
        environment = values.get('environment', 'development')
        if environment == 'production' and len(v) < 32:
            print("❌ SECURITY ERROR: JWT_SECRET_KEY must be at least 32 characters in production")
            print("   Generate with: openssl rand -hex 32")
            sys.exit(1)
        return v

    @validator('ghl_webhook_secret')
    def validate_webhook_secret(cls, v, values):
        """SECURITY FIX: Validate webhook secret in production."""
        environment = values.get('environment', 'development')
        if environment == 'production' and not v:
            print("❌ SECURITY ERROR: GHL_WEBHOOK_SECRET is required in production")
            print("   Generate with: openssl rand -hex 32")
            sys.exit(1)
        if v and len(v) < 32:
            print("⚠️  WARNING: Webhook secret should be at least 32 characters")
        return v

    @validator('anthropic_api_key')
    def validate_anthropic_key(cls, v):
        """Validate Anthropic API key format."""
        if v and not v.startswith('sk-ant-'):
            print("⚠️  WARNING: Anthropic API key should start with 'sk-ant-'")
        return v

    @validator('ghl_api_key')
    def validate_ghl_key(cls, v, values):
        """Validate GHL API key format."""
        if v and not v.startswith('eyJ'):
            print("⚠️  WARNING: GHL API key should be JWT format (starts with 'eyJ')")
        return v

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False
    )


# Global settings instance
# This will be imported throughout the application
settings = Settings()


# Environment Mode Detection
class EnvironmentMode(Enum):
    """Application environment modes"""
    DEMO = "demo"           # Mock data, no API calls (default)
    STAGING = "staging"     # Real API, test account
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
            "banner_type": "info"
        }
    elif env == EnvironmentMode.STAGING:
        return {
            "icon": "🧪",
            "name": "Staging Mode",
            "color": "#3B82F6",
            "message": "Connected to test environment.",
            "banner_type": "info"
        }
    else:  # PRODUCTION
        return {
            "icon": "✅",
            "name": "Live Mode",
            "color": "#10B981",
            "message": "Connected to GoHighLevel production.",
            "banner_type": "success"
        }
