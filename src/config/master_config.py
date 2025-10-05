"""
Master Configuration System
Consolidates all configuration sources into single source of truth.

Copyright (c) 2025 Faceless YouTube Automation Platform
Licensed under GNU AGPL v3.0
"""

from pathlib import Path
from typing import Optional, Dict, Any, List
import os
import sys

# Conditional import based on pydantic version
try:
    from pydantic_settings import BaseSettings
    from pydantic import Field
except ImportError:
    from pydantic import BaseSettings, Field

from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class DatabaseConfig(BaseSettings):
    """Database connection settings."""
    
    postgres_host: str = Field(default="localhost", env="DB_HOST")
    postgres_port: int = Field(default=5432, env="DB_PORT")
    postgres_user: str = Field(default="postgres", env="DB_USER")
    postgres_password: str = Field(default="", env="DB_PASSWORD")
    postgres_db: str = Field(default="faceless_youtube", env="DB_NAME")
    
    mongodb_host: str = Field(default="localhost", env="MONGO_HOST")
    mongodb_port: int = Field(default=27017, env="MONGO_PORT")
    mongodb_db: str = Field(default="faceless_youtube", env="MONGO_DB")
    
    redis_host: str = Field(default="localhost", env="REDIS_HOST")
    redis_port: int = Field(default=6379, env="REDIS_PORT")
    redis_db: int = Field(default=0, env="REDIS_DB")
    
    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "ignore"  # Ignore extra fields from .env
    
    @property
    def postgres_url(self) -> str:
        """Get PostgreSQL connection URL."""
        return (
            f"postgresql://{self.postgres_user}:{self.postgres_password}@"
            f"{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )
    
    @property
    def mongodb_url(self) -> str:
        """Get MongoDB connection URL."""
        return f"mongodb://{self.mongodb_host}:{self.mongodb_port}/{self.mongodb_db}"
    
    @property
    def redis_url(self) -> str:
        """Get Redis connection URL."""
        return f"redis://{self.redis_host}:{self.redis_port}/{self.redis_db}"


class PathConfig(BaseSettings):
    """File system paths."""
    
    # Dynamically determine project root
    project_root: Path = Field(default_factory=lambda: Path(__file__).parent.parent.parent)
    
    class Config:
        arbitrary_types_allowed = True
        env_file = ".env"
        extra = "ignore"  # Ignore extra fields from .env
    
    @property
    def assets_dir(self) -> Path:
        """Assets directory path."""
        return self.project_root / "assets"
    
    @property
    def video_assets(self) -> Path:
        """Video assets path."""
        return self.assets_dir / "videos"
    
    @property
    def audio_assets(self) -> Path:
        """Audio assets path."""
        return self.assets_dir / "audio"
    
    @property
    def fonts_dir(self) -> Path:
        """Fonts directory path."""
        return self.assets_dir / "fonts"
    
    @property
    def output_dir(self) -> Path:
        """Output videos directory."""
        return self.project_root / "output_videos"
    
    @property
    def temp_dir(self) -> Path:
        """Temporary files directory."""
        return self.project_root / "temp"
    
    @property
    def cache_dir(self) -> Path:
        """Cache directory."""
        return self.project_root / "cache"
    
    @property
    def scripts_dir(self) -> Path:
        """Scripts storage directory."""
        return self.project_root / "scripts"
    
    @property
    def tokens_dir(self) -> Path:
        """OAuth tokens directory."""
        return self.project_root / "youtube_tokens"
    
    def ensure_directories(self):
        """Create all required directories if they don't exist."""
        directories = [
            self.assets_dir,
            self.video_assets,
            self.audio_assets,
            self.fonts_dir,
            self.output_dir,
            self.temp_dir,
            self.cache_dir,
            self.scripts_dir,
            self.tokens_dir,
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)


class APIConfig(BaseSettings):
    """External API credentials."""
    
    # YouTube
    youtube_client_secrets: str = Field(
        default="client_secrets.json",
        env="YOUTUBE_CLIENT_SECRETS"
    )
    
    # Pexels
    pexels_api_key: Optional[str] = Field(default=None, env="PEXELS_API_KEY")
    
    # Pixabay
    pixabay_api_key: Optional[str] = Field(default=None, env="PIXABAY_API_KEY")
    
    # Ollama
    ollama_host: str = Field(default="localhost", env="OLLAMA_HOST")
    ollama_port: int = Field(default=11434, env="OLLAMA_PORT")
    ollama_model: str = Field(default="mistral", env="OLLAMA_MODEL")
    
    # OpenAI (optional)
    openai_api_key: Optional[str] = Field(default=None, env="OPENAI_API_KEY")
    
    # ElevenLabs (optional)
    elevenlabs_api_key: Optional[str] = Field(default=None, env="ELEVENLABS_API_KEY")
    
    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "ignore"  # Ignore extra fields from .env


class ApplicationConfig(BaseSettings):
    """Main application settings."""
    
    app_name: str = Field(default="Faceless YouTube Automation", env="APP_NAME")
    app_version: str = Field(default="2.0.0", env="APP_VERSION")
    debug: bool = Field(default=False, env="DEBUG")
    
    # API settings
    api_host: str = Field(default="127.0.0.1", env="API_HOST")  # Secure default, override for production
    api_port: int = Field(default=8000, env="API_PORT")
    api_workers: int = Field(default=4, env="API_WORKERS")
    
    # Frontend settings
    frontend_port: int = Field(default=3000, env="FRONTEND_PORT")
    
    # Security
    secret_key: str = Field(
        default="CHANGE_THIS_IN_PRODUCTION_USE_CRYPTOGRAPHICALLY_SECURE_KEY",
        env="SECRET_KEY"
    )
    cors_origins: str = Field(
        default="http://localhost:3000,http://localhost:8000",
        env="CORS_ORIGINS"
    )
    
    # Performance
    max_concurrent_jobs: int = Field(default=2, env="MAX_CONCURRENT_JOBS")
    cache_ttl: int = Field(default=3600, env="CACHE_TTL")
    
    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "ignore"  # Ignore extra fields from .env
    
    @property
    def cors_origins_list(self) -> List[str]:
        """Get CORS origins as a list."""
        return [origin.strip() for origin in self.cors_origins.split(',')]


class MasterConfig:
    """
    Master configuration object consolidating all settings.
    
    Usage:
        from src.config.master_config import config
        
        print(config.database.postgres_url)
        print(config.paths.output_dir)
        print(config.api.ollama_host)
    """
    
    def __init__(self):
        self.database = DatabaseConfig()
        self.paths = PathConfig()
        self.api = APIConfig()
        self.app = ApplicationConfig()
        
        # Ensure all directories exist
        self.paths.ensure_directories()
    
    def to_dict(self) -> Dict[str, Any]:
        """Export all configuration as dictionary."""
        return {
            "database": self.database.dict(),
            "paths": {
                "project_root": str(self.paths.project_root),
                "assets_dir": str(self.paths.assets_dir),
                "video_assets": str(self.paths.video_assets),
                "audio_assets": str(self.paths.audio_assets),
                "fonts_dir": str(self.paths.fonts_dir),
                "output_dir": str(self.paths.output_dir),
                "temp_dir": str(self.paths.temp_dir),
                "cache_dir": str(self.paths.cache_dir),
                "scripts_dir": str(self.paths.scripts_dir),
                "tokens_dir": str(self.paths.tokens_dir),
            },
            "api": self.api.dict(),
            "app": self.app.dict()
        }
    
    def validate(self) -> Dict[str, list]:
        """
        Validate all configuration and return issues.
        
        Returns:
            Dictionary with 'errors' and 'warnings' lists
        """
        errors = []
        warnings = []
        
        # Check critical files exist
        youtube_secrets_path = self.paths.project_root / self.api.youtube_client_secrets
        if not youtube_secrets_path.exists():
            errors.append(
                f"YouTube client secrets not found: {youtube_secrets_path}"
            )
        
        # Check database configuration
        if not self.database.postgres_password:
            warnings.append("PostgreSQL password not set")
        
        # Check API keys
        if not self.api.pexels_api_key:
            warnings.append("Pexels API key not set (video assets limited)")
        
        if not self.api.pixabay_api_key:
            warnings.append("Pixabay API key not set (video assets limited)")
        
        # Check secret key
        if "CHANGE_THIS" in self.app.secret_key:
            warnings.append("Secret key is using default value - INSECURE for production!")
        
        # Check debug mode
        if self.app.debug:
            warnings.append("Debug mode is enabled - disable for production!")
        
        return {
            "errors": errors,
            "warnings": warnings
        }
    
    def print_config(self):
        """Print current configuration (hiding sensitive data)."""
        print("\n" + "="*60)
        print("FACELESS YOUTUBE AUTOMATION - CONFIGURATION")
        print("="*60)
        
        print(f"\nApplication:")
        print(f"  Name: {self.app.app_name}")
        print(f"  Version: {self.app.app_version}")
        print(f"  Debug: {self.app.debug}")
        
        print(f"\nAPI Server:")
        print(f"  Host: {self.app.api_host}")
        print(f"  Port: {self.app.api_port}")
        print(f"  Workers: {self.app.api_workers}")
        
        print(f"\nDatabase:")
        print(f"  PostgreSQL: {self.database.postgres_host}:{self.database.postgres_port}/{self.database.postgres_db}")
        print(f"  MongoDB: {self.database.mongodb_host}:{self.database.mongodb_port}/{self.database.mongodb_db}")
        print(f"  Redis: {self.database.redis_host}:{self.database.redis_port}/{self.database.redis_db}")
        
        print(f"\nPaths:")
        print(f"  Project Root: {self.paths.project_root}")
        print(f"  Assets: {self.paths.assets_dir}")
        print(f"  Output: {self.paths.output_dir}")
        print(f"  Cache: {self.paths.cache_dir}")
        
        print(f"\nExternal APIs:")
        print(f"  Ollama: http://{self.api.ollama_host}:{self.api.ollama_port} (model: {self.api.ollama_model})")
        print(f"  Pexels: {'✅ Configured' if self.api.pexels_api_key else '❌ Not configured'}")
        print(f"  Pixabay: {'✅ Configured' if self.api.pixabay_api_key else '❌ Not configured'}")
        print(f"  OpenAI: {'✅ Configured' if self.api.openai_api_key else '❌ Not configured'}")
        print(f"  ElevenLabs: {'✅ Configured' if self.api.elevenlabs_api_key else '❌ Not configured'}")
        
        # Validation
        validation = self.validate()
        if validation['errors']:
            print(f"\n❌ ERRORS ({len(validation['errors'])}):")
            for error in validation['errors']:
                print(f"  - {error}")
        
        if validation['warnings']:
            print(f"\n⚠️ WARNINGS ({len(validation['warnings'])}):")
            for warning in validation['warnings']:
                print(f"  - {warning}")
        
        if not validation['errors'] and not validation['warnings']:
            print("\n✅ Configuration validated successfully!")
        
        print("="*60 + "\n")


# Global configuration instance
config = MasterConfig()


# Convenience function
def get_config() -> MasterConfig:
    """Get global configuration instance."""
    return config


# CLI for testing configuration
if __name__ == "__main__":
    """Test configuration when run directly."""
    config.print_config()
    
    # Test directory creation
    print("\nTesting directory creation...")
    config.paths.ensure_directories()
    print("✅ All directories created/verified")
    
    # Export to JSON
    if len(sys.argv) > 1 and sys.argv[1] == "--export":
        import json
        config_dict = config.to_dict()
        with open("config_export.json", "w") as f:
            json.dump(config_dict, f, indent=2, default=str)
        print("\n✅ Configuration exported to config_export.json")
