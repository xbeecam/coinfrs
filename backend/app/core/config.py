from pydantic import BaseSettings, validator, PostgresDsn, RedisDsn
from typing import Optional, Dict, Any
import secrets


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.
    """
    
    # Application
    APP_NAME: str = "Coinfrs"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = False
    
    # API
    API_V1_PREFIX: str = "/api/v1"
    
    # Security
    SECRET_KEY: str = secrets.token_urlsafe(32)
    ENCRYPTION_KEY: str = ""  # Must be set in production
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    ALGORITHM: str = "HS256"
    
    # Database
    DATABASE_URL: PostgresDsn = "postgresql://user:password@localhost/coinfrs"
    
    @validator("DATABASE_URL", pre=True)
    def build_database_url(cls, v: str, values: Dict[str, Any]) -> str:
        if isinstance(v, str):
            return v
        # Build from components if needed
        return PostgresDsn.build(
            scheme="postgresql",
            user=values.get("POSTGRES_USER", "user"),
            password=values.get("POSTGRES_PASSWORD", "password"),
            host=values.get("POSTGRES_HOST", "localhost"),
            port=values.get("POSTGRES_PORT", "5432"),
            path=f"/{values.get('POSTGRES_DB', 'coinfrs')}",
        )
    
    # Redis
    REDIS_URL: RedisDsn = "redis://localhost:6379/0"
    
    # Celery
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/0"
    
    # OAuth
    GOOGLE_CLIENT_ID: Optional[str] = None
    GOOGLE_CLIENT_SECRET: Optional[str] = None
    
    # Email (for OTP)
    EMAIL_HOST: Optional[str] = None
    EMAIL_PORT: Optional[int] = 587
    EMAIL_USERNAME: Optional[str] = None
    EMAIL_PASSWORD: Optional[str] = None
    EMAIL_FROM: Optional[str] = "noreply@coinfrs.com"
    
    # CORS
    BACKEND_CORS_ORIGINS: list[str] = ["http://localhost:3000", "http://localhost:8000"]
    
    @validator("BACKEND_CORS_ORIGINS", pre=True)
    def assemble_cors_origins(cls, v: str | list[str]) -> list[str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)
    
    # Monitoring
    SENTRY_DSN: Optional[str] = None
    
    # Binance (for development/testing)
    BINANCE_API_KEY: Optional[str] = None
    BINANCE_API_SECRET: Optional[str] = None
    
    # Fireblocks (for development/testing)
    FIREBLOCKS_API_KEY: Optional[str] = None
    FIREBLOCKS_API_SECRET: Optional[str] = None
    
    @validator("ENCRYPTION_KEY", pre=True)
    def validate_encryption_key(cls, v: str) -> str:
        if not v and not cls.DEBUG:
            raise ValueError("ENCRYPTION_KEY must be set in production")
        return v
    
    class Config:
        env_file = ".env"
        case_sensitive = True


# Create global settings instance
settings = Settings()