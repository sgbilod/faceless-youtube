"""
Configuration module for Faceless YouTube Automation Platform.

Provides centralized configuration management for all services.

Usage:
    from src.config import config
    
    # Access configuration
    db_url = config.database.postgres_url
    output_path = config.paths.output_dir
    ollama_host = config.api.ollama_host
"""

from .master_config import (
    config,
    get_config,
    MasterConfig,
    DatabaseConfig,
    PathConfig,
    APIConfig,
    ApplicationConfig,
)

__all__ = [
    "config",
    "get_config",
    "MasterConfig",
    "DatabaseConfig",
    "PathConfig",
    "APIConfig",
    "ApplicationConfig",
]
