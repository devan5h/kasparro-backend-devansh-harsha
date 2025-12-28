"""Configuration management using Pydantic settings."""
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Database
    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/kasparoo_db"
    
    # API Keys
    COINPAPRIKA_API_KEY: Optional[str] = None
    
    # API Settings
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    
    # ETL Settings
    ETL_BATCH_SIZE: int = 100
    ETL_RUN_INTERVAL_SECONDS: int = 300  # 5 minutes
    
    # Rate Limiting
    COINPAPRIKA_RATE_LIMIT: int = 10  # requests per second
    COINGECKO_RATE_LIMIT: int = 10
    
    # Retry Settings
    MAX_RETRIES: int = 3
    RETRY_BACKOFF_FACTOR: float = 2.0
    
    # Logging
    LOG_LEVEL: str = "INFO"
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()

