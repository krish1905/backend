"""Application configuration."""
from pydantic_settings import BaseSettings
from typing import List, Optional
from decimal import Decimal
import os


class Settings(BaseSettings):
    """Application settings."""
    
    # NOT USING SUPABASE - using local JWT authentication
    supabase_url: str = "not-used"
    supabase_service_role_key: str = "not-used"
    supabase_anon_key: str = "not-used"
    
    # Database - SQLite for serverless (Vercel compatible)
    # In Vercel, we'll use libsql or Turso for persistence
    database_url: str = "sqlite:///tmp/financial_app.db"
    
    # Server
    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = True
    
    # CORS
    allowed_origins: str = "http://localhost:3000"
    
    # Transfer Limits
    min_transfer_amount: Decimal = Decimal("0.01")
    max_transfer_amount: Decimal = Decimal("10000.00")
    
    # Application
    app_name: str = "Financial P2P API"
    app_version: str = "1.0.0"
    
    @property
    def allowed_origins_list(self) -> List[str]:
        """Get list of allowed origins."""
        return [origin.strip() for origin in self.allowed_origins.split(",")]
    
    @property
    def is_configured(self) -> bool:
        """Check if Supabase is properly configured (we're not using it)."""
        return False  # Always use local auth
    
    class Config:
        """Pydantic config."""
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


# Create settings instance
settings = Settings()


# Info message about auth mode
if not settings.is_configured and not os.getenv("SKIP_CONFIG_WARNING"):
    import logging
    logger = logging.getLogger(__name__)
    logger.info("="*70)
    logger.info(" Running in DEVELOPMENT MODE (Local Authentication)")
    logger.info("="*70)
    logger.info(" ✓ No Supabase setup required")
    logger.info(" ✓ Using local JWT authentication")
    logger.info(" ✓ Using SQLite database")
    logger.info(" ✓ Full signup/login working out of the box!")
    logger.info("")
    logger.info(" To switch to Supabase (optional):")
    logger.info("   1. Create .env file with Supabase credentials")
    logger.info("   2. Restart the server")
    logger.info("="*70)

