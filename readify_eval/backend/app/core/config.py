"""
Configuration management using PyYAML with optional Nacos config center support.

Loading strategy:
- NACOS disabled (default): load everything from local config.yaml
- NACOS enabled: read nacos/service blocks from config.yaml for connection params,
  then pull app/database/cors/logging from Nacos config center and replace local values.
"""
import asyncio
import logging
import os
from typing import Any, Dict, List, Optional
from functools import lru_cache

import yaml
from pydantic import BaseModel

try:
    from v2.nacos import ClientConfig, ConfigParam, NacosConfigService  # type: ignore
except Exception:  # pragma: no cover - nacos-sdk not installed
    ClientConfig = None  # type: ignore
    ConfigParam = None  # type: ignore
    NacosConfigService = None  # type: ignore

logger = logging.getLogger(__name__)


class AppConfig(BaseModel):
    """Application configuration"""
    name: str
    version: str
    description: str
    debug: bool = False
    host: str = "0.0.0.0"
    port: int = 8082


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


class NacosConfig(BaseModel):
    """Nacos service registration and config center settings"""
    enabled: bool = False
    server_addr: str = "localhost:8848"
    namespace: str = ""
    group: str = "DEFAULT_GROUP"
    username: str = "nacos"
    password: str = "nacos"
    cluster: str = "DEFAULT"
    heartbeat_interval: int = 5
    config_data_id: str = ""


class ServiceConfig(BaseModel):
    """Service identity for Nacos registration"""
    name: str = "readify-eval"
    host: str = ""  # empty = auto-detect
    port: int = 8082


class Settings(BaseModel):
    """Main settings class"""
    app: AppConfig
    database: DatabaseConfig
    cors: CORSConfig
    logging: LoggingConfig
    nacos: NacosConfig = NacosConfig()
    service: ServiceConfig = ServiceConfig()


def _read_yaml(config_path: str = "config.yaml") -> Dict[str, Any]:
    """Read raw YAML config file and return as dict."""
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Configuration file not found: {config_path}")
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def _load_nacos_config(nacos_cfg: Dict[str, Any]) -> Dict[str, Any]:
    """
    Pull configuration from Nacos Config Center.

    Args:
        nacos_cfg: The 'nacos' section parsed from local config.yaml

    Returns:
        Remote config dict (app/database/cors/logging) or empty dict on failure.
    """
    data_id = nacos_cfg.get("config_data_id", "").strip()
    group = nacos_cfg.get("group", "DEFAULT_GROUP")
    server_addr = nacos_cfg.get("server_addr", "127.0.0.1:8848")
    namespace = nacos_cfg.get("namespace", "")
    username = nacos_cfg.get("username", "nacos")
    password = nacos_cfg.get("password", "nacos")

    if not data_id:
        return {}
    if NacosConfigService is None or ClientConfig is None or ConfigParam is None:
        logger.warning("Nacos config not loaded (missing nacos-sdk-python or PyYAML)")
        return {}

    async def _pull() -> Dict[str, Any]:
        client_config = ClientConfig(
            server_addresses=server_addr,
            namespace_id=namespace,
            username=username,
            password=password,
        )
        config_service = await NacosConfigService.create_config_service(client_config)
        content = await config_service.get_config(ConfigParam(data_id=data_id, group=group))
        try:
            loaded = yaml.safe_load(content) or {}
            if not isinstance(loaded, dict):
                raise ValueError("config content is not a mapping")
            return loaded
        except Exception as exc:
            logger.error("Failed to parse Nacos config %s/%s: %s", group, data_id, exc)
            return {}

    try:
        return asyncio.run(_pull())
    except Exception as exc:
        logger.error("Failed to fetch Nacos config %s/%s: %s", group, data_id, exc)
        return {}


def load_config(config_path: str = "config.yaml") -> Settings:
    """
    Load configuration with optional Nacos override.

    1. Read local config.yaml (always needed for nacos/service connection params).
    2. If nacos.enabled is true, pull remote config and replace app/database/cors/logging.
    3. Otherwise use local config.yaml as-is.
    """
    local_data = _read_yaml(config_path)

    nacos_section = local_data.get("nacos", {})
    nacos_enabled = nacos_section.get("enabled", False)

    if nacos_enabled:
        remote_data = _load_nacos_config(nacos_section)
        if not remote_data:
            raise RuntimeError(
                "nacos.enabled=true 但未能从 Nacos 拉取到配置，请检查 "
                "config_data_id、group、namespace、username、password 等配置是否正确"
            )
        # Remote config replaces app/database/cors/logging blocks
        # Keep nacos and service from local config.yaml
        merged = {**remote_data}
        merged["nacos"] = nacos_section
        merged.setdefault("service", local_data.get("service", {}))
        return Settings(**merged)
    else:
        return Settings(**local_data)


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
