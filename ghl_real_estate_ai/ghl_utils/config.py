"""
Configuration module for GHL Real Estate AI.

Manages environment variables and application settings using Pydantic.
"""
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional
from enum import Enum
import os


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
    claude_model: str = "claude-sonnet-4-20250514"
    temperature: float = 0.7
    max_tokens: int = 150
    default_llm_provider: str = "claude"
    gemini_model: Optional[str] = None
    google_api_key: Optional[str] = None

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

    # Activation & Trigger Settings
    activation_tags: list[str] = ["Hit List", "Need to Qualify", "Needs Qualifying"]
    deactivation_tags: list[str] = ["AI-Off", "Qualified", "Stop-Bot"]
    required_contact_type: Optional[str] = "Seller"
    disposition_field_name: str = "disposition"
    bot_active_disposition: str = "Hit List"

    # GHL Workflow & Custom Field Mapping
    notify_agent_workflow_id: Optional[str] = None
    ghl_calendar_id: Optional[str] = None
    custom_field_lead_score: Optional[str] = None
    custom_field_budget: Optional[str] = None
    custom_field_location: Optional[str] = None
    custom_field_timeline: Optional[str] = None

    # Performance Settings
    webhook_timeout_seconds: int = 3
    max_conversation_history_length: int = 20
    previous_context_window_hours: int = 24
    rag_top_k_results: int = 3

    # Enhanced Batched Processing Settings (Phase 3 Enhancement)
    enable_webhook_batching: bool = True  # Master toggle for batched processing
    webhook_max_batch_size: int = 5  # Maximum webhooks per batch
    webhook_batch_timeout_seconds: float = 1.5  # Max time to wait for batch completion
    webhook_batching_threshold: int = 2  # Minimum events to consider batching
    webhook_conversation_window: float = 10.0  # Seconds to group conversation messages
    webhook_location_window: float = 2.0  # Seconds to group location messages

    # Security
    ghl_webhook_secret: Optional[str] = None  # For signature verification

    # Testing
    test_mode: bool = False

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
