"""
Settings configuration for Autonomous Document Processing Platform.
Adapted from EnterpriseHub's proven configuration patterns.
"""

from functools import lru_cache
from typing import Optional, List, Dict, Any
import os
from pydantic import BaseSettings, validator, Field


class Settings(BaseSettings):
    """
    Application settings with document processing specific configurations.
    """

    # ==============================================================================
    # Application Core
    # ==============================================================================
    app_name: str = "Autonomous Document Platform"
    app_version: str = "1.0.0"
    environment: str = Field(default="development", env="ENVIRONMENT")
    debug: bool = Field(default=False, env="DEBUG")
    log_level: str = Field(default="INFO", env="LOG_LEVEL")

    # ==============================================================================
    # API Configuration
    # ==============================================================================
    api_host: str = Field(default="0.0.0.0", env="API_HOST")
    api_port: int = Field(default=8000, env="API_PORT")
    api_workers: int = Field(default=4, env="API_WORKERS")

    # ==============================================================================
    # AI/LLM Configuration (Inherited from EnterpriseHub patterns)
    # ==============================================================================
    anthropic_api_key: str = Field(env="ANTHROPIC_API_KEY")
    openai_api_key: Optional[str] = Field(default=None, env="OPENAI_API_KEY")
    google_api_key: Optional[str] = Field(default=None, env="GOOGLE_API_KEY")

    # Model routing for document processing
    default_model: str = Field(default="claude-3-5-sonnet-20241022", env="DEFAULT_MODEL")
    vision_model: str = Field(default="claude-3-5-sonnet-20241022", env="VISION_MODEL")
    fast_model: str = Field(default="claude-3-haiku-20240307", env="FAST_MODEL")

    # Token limits and costs
    max_tokens_per_request: int = Field(default=4096, env="MAX_TOKENS_PER_REQUEST")
    max_context_length: int = Field(default=200000, env="MAX_CONTEXT_LENGTH")

    # ==============================================================================
    # Database Configuration (PostgreSQL for document metadata)
    # ==============================================================================
    database_url: str = Field(env="DATABASE_URL")
    database_pool_size: int = Field(default=20, env="DATABASE_POOL_SIZE")
    database_max_overflow: int = Field(default=30, env="DATABASE_MAX_OVERFLOW")
    database_pool_timeout: int = Field(default=30, env="DATABASE_POOL_TIMEOUT")

    # ==============================================================================
    # Redis Configuration (Adapted from EnterpriseHub cache patterns)
    # ==============================================================================
    redis_host: str = Field(default="localhost", env="REDIS_HOST")
    redis_port: int = Field(default=6379, env="REDIS_PORT")
    redis_password: Optional[str] = Field(default=None, env="REDIS_PASSWORD")
    redis_db: int = Field(default=0, env="REDIS_DB")
    redis_ssl: bool = Field(default=False, env="REDIS_SSL")
    redis_pool_size: int = Field(default=50, env="REDIS_POOL_SIZE")

    # Cache TTL settings
    cache_ttl_document: int = Field(default=3600, env="CACHE_TTL_DOCUMENT")  # 1 hour
    cache_ttl_extraction: int = Field(default=1800, env="CACHE_TTL_EXTRACTION")  # 30 min
    cache_ttl_template: int = Field(default=7200, env="CACHE_TTL_TEMPLATE")  # 2 hours

    # ==============================================================================
    # Document Storage Configuration
    # ==============================================================================
    storage_backend: str = Field(default="minio", env="STORAGE_BACKEND")  # minio, s3, local

    # MinIO/S3 Configuration
    storage_endpoint: Optional[str] = Field(default="localhost:9000", env="STORAGE_ENDPOINT")
    storage_access_key: str = Field(env="STORAGE_ACCESS_KEY")
    storage_secret_key: str = Field(env="STORAGE_SECRET_KEY")
    storage_bucket_name: str = Field(default="documents", env="STORAGE_BUCKET_NAME")
    storage_region: str = Field(default="us-east-1", env="STORAGE_REGION")
    storage_secure: bool = Field(default=False, env="STORAGE_SECURE")

    # Local storage (for development)
    local_storage_path: str = Field(default="./storage/documents", env="LOCAL_STORAGE_PATH")

    # ==============================================================================
    # Document Processing Configuration
    # ==============================================================================
    # File size limits
    max_file_size_mb: int = Field(default=100, env="MAX_FILE_SIZE_MB")
    max_pages_per_document: int = Field(default=500, env="MAX_PAGES_PER_DOCUMENT")
    max_batch_size: int = Field(default=100, env="MAX_BATCH_SIZE")

    # Supported file formats
    supported_formats: List[str] = Field(
        default=["pdf", "docx", "xlsx", "pptx", "png", "jpg", "jpeg", "tiff"],
        env="SUPPORTED_FORMATS"
    )

    # OCR Configuration
    ocr_engine: str = Field(default="tesseract", env="OCR_ENGINE")  # tesseract, aws_textract, google_vision
    tesseract_path: Optional[str] = Field(default=None, env="TESSERACT_PATH")
    ocr_confidence_threshold: float = Field(default=0.7, env="OCR_CONFIDENCE_THRESHOLD")

    # Document processing timeouts
    processing_timeout_seconds: int = Field(default=300, env="PROCESSING_TIMEOUT_SECONDS")
    ocr_timeout_seconds: int = Field(default=120, env="OCR_TIMEOUT_SECONDS")
    llm_timeout_seconds: int = Field(default=60, env="LLM_TIMEOUT_SECONDS")

    # ==============================================================================
    # Queue Configuration (Celery for background processing)
    # ==============================================================================
    celery_broker_url: str = Field(env="CELERY_BROKER_URL", default="redis://localhost:6379/1")
    celery_result_backend: str = Field(env="CELERY_RESULT_BACKEND", default="redis://localhost:6379/2")
    celery_worker_concurrency: int = Field(default=4, env="CELERY_WORKER_CONCURRENCY")

    # ==============================================================================
    # Security Configuration (Inherited from EnterpriseHub)
    # ==============================================================================
    secret_key: str = Field(env="SECRET_KEY")
    jwt_algorithm: str = Field(default="HS256", env="JWT_ALGORITHM")
    jwt_access_token_expire_minutes: int = Field(default=480, env="JWT_ACCESS_TOKEN_EXPIRE_MINUTES")

    # Rate limiting
    rate_limit_per_minute: int = Field(default=100, env="RATE_LIMIT_PER_MINUTE")
    rate_limit_burst: int = Field(default=200, env="RATE_LIMIT_BURST")

    # Document encryption
    document_encryption_key: Optional[str] = Field(default=None, env="DOCUMENT_ENCRYPTION_KEY")
    encrypt_documents_at_rest: bool = Field(default=True, env="ENCRYPT_DOCUMENTS_AT_REST")

    # ==============================================================================
    # Legal & Compliance Configuration
    # ==============================================================================
    retention_policy_days: int = Field(default=2555, env="RETENTION_POLICY_DAYS")  # 7 years
    audit_log_retention_days: int = Field(default=365, env="AUDIT_LOG_RETENTION_DAYS")  # 1 year

    # PII detection
    enable_pii_detection: bool = Field(default=True, env="ENABLE_PII_DETECTION")
    pii_confidence_threshold: float = Field(default=0.8, env="PII_CONFIDENCE_THRESHOLD")

    # ==============================================================================
    # Monitoring & Analytics
    # ==============================================================================
    enable_metrics: bool = Field(default=True, env="ENABLE_METRICS")
    metrics_port: int = Field(default=9090, env="METRICS_PORT")

    sentry_dsn: Optional[str] = Field(default=None, env="SENTRY_DSN")
    enable_performance_monitoring: bool = Field(default=True, env="ENABLE_PERFORMANCE_MONITORING")

    # ==============================================================================
    # Client Portal Configuration
    # ==============================================================================
    streamlit_host: str = Field(default="0.0.0.0", env="STREAMLIT_HOST")
    streamlit_port: int = Field(default=8501, env="STREAMLIT_PORT")
    streamlit_theme: str = Field(default="light", env="STREAMLIT_THEME")

    # Session configuration
    session_timeout_minutes: int = Field(default=60, env="SESSION_TIMEOUT_MINUTES")
    max_concurrent_sessions: int = Field(default=1000, env="MAX_CONCURRENT_SESSIONS")

    @validator("anthropic_api_key", "secret_key", "storage_access_key", "storage_secret_key")
    def validate_required_secrets(cls, v, field):
        """Validate that required secrets are provided."""
        if not v:
            raise ValueError(f"{field.name} is required")
        return v

    @validator("max_file_size_mb")
    def validate_file_size(cls, v):
        """Validate file size limits."""
        if v <= 0 or v > 1000:  # Max 1GB
            raise ValueError("max_file_size_mb must be between 1 and 1000 MB")
        return v

    @validator("supported_formats")
    def validate_formats(cls, v):
        """Validate supported file formats."""
        allowed_formats = {"pdf", "docx", "xlsx", "pptx", "png", "jpg", "jpeg", "tiff", "txt", "csv"}
        for fmt in v:
            if fmt.lower() not in allowed_formats:
                raise ValueError(f"Unsupported format: {fmt}")
        return [fmt.lower() for fmt in v]

    @property
    def redis_url(self) -> str:
        """Construct Redis URL from components."""
        auth = f":{self.redis_password}@" if self.redis_password else ""
        protocol = "rediss" if self.redis_ssl else "redis"
        return f"{protocol}://{auth}{self.redis_host}:{self.redis_port}/{self.redis_db}"

    @property
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.environment.lower() == "production"

    @property
    def document_storage_config(self) -> Dict[str, Any]:
        """Get storage configuration based on backend."""
        if self.storage_backend == "s3":
            return {
                "backend": "s3",
                "access_key": self.storage_access_key,
                "secret_key": self.storage_secret_key,
                "bucket_name": self.storage_bucket_name,
                "region": self.storage_region
            }
        elif self.storage_backend == "minio":
            return {
                "backend": "minio",
                "endpoint": self.storage_endpoint,
                "access_key": self.storage_access_key,
                "secret_key": self.storage_secret_key,
                "bucket_name": self.storage_bucket_name,
                "secure": self.storage_secure
            }
        else:  # local
            return {
                "backend": "local",
                "path": self.local_storage_path
            }

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    """
    Get cached application settings.
    Uses LRU cache to avoid re-reading environment variables.
    """
    return Settings()