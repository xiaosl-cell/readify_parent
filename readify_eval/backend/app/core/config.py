"""
Configuration management using PyYAML
"""
import os
from typing import List, Optional
from functools import lru_cache
import yaml
from pydantic import BaseModel
from pydantic_settings import BaseSettings


class AppConfig(BaseModel):
    """Application configuration"""
    name: str
    version: str
    description: str
    debug: bool = False
    host: str = "0.0.0.0"
    port: int = 8000


class DatabaseConfig(BaseModel):
    """Database configuration"""
    url: str
    echo: bool = False
    pool_size: int = 5
    max_overflow: int = 10
    pool_pre_ping: bool = True


class CORSConfig(BaseModel):
    """CORS configuration"""
    allow_origins: List[str] = ["*"]
    allow_credentials: bool = True
    allow_methods: List[str] = ["*"]
    allow_headers: List[str] = ["*"]


class LoggingConfig(BaseModel):
    """Logging configuration"""
    level: str = "INFO"
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    log_dir: str = "logs"
    log_file: str = "app.log"
    backup_count: int = 30
    console_output: bool = True
    console_level: Optional[str] = None  # If None, uses 'level'
    file_level: Optional[str] = None  # If None, uses 'level'


class Settings(BaseSettings):
    """Main settings class"""
    app: AppConfig
    database: DatabaseConfig
    cors: CORSConfig
    logging: LoggingConfig

    class Config:
        case_sensitive = False


def load_config(config_path: str = "config.yaml") -> Settings:
    """
    Load configuration from YAML file
    
    Args:
        config_path: Path to the YAML configuration file
        
    Returns:
        Settings object with all configurations
    """
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Configuration file not found: {config_path}")
    
    with open(config_path, 'r', encoding='utf-8') as f:
        config_data = yaml.safe_load(f)
    
    return Settings(**config_data)


@lru_cache()
def get_settings() -> Settings:
    """
    Get cached settings instance
    
    Returns:
        Settings object (cached)
    """
    return load_config()


# Create a global settings instance
settings = get_settings()

