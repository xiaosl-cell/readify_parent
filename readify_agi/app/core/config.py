# 标准库导入
import asyncio
import logging
import os
from typing import Any, Dict

# 第三方库导入
from dotenv import load_dotenv
from pydantic_settings import BaseSettings

try:
    import yaml
except ImportError:
    yaml = None  # type: ignore

try:
    from v2.nacos import ClientConfig, ConfigParam, NacosConfigService  # type: ignore
except Exception:  # pragma: no cover - nacos-sdk not installed
    ClientConfig = None  # type: ignore
    ConfigParam = None  # type: ignore
    NacosConfigService = None  # type: ignore

logger = logging.getLogger(__name__)

# Load .env early so NACOS_* flags are visible before Settings instantiation
load_dotenv()


def _load_nacos_config() -> Dict[str, Any]:
    """Optionally pull configuration from Nacos Config and return as dict."""
    enabled = os.getenv("NACOS_ENABLED", "false").lower() == "true"
    data_id = os.getenv("NACOS_CONFIG_DATA_ID", "").strip()
    group = os.getenv("NACOS_GROUP", "DEFAULT_GROUP")
    server_addr = os.getenv("NACOS_SERVER_ADDR", "127.0.0.1:8848")
    namespace = os.getenv("NACOS_NAMESPACE", "")
    username = os.getenv("NACOS_USERNAME", "nacos")
    password = os.getenv("NACOS_PASSWORD", "nacos")

    if not enabled or not data_id:
        return {}
    if yaml is None or NacosConfigService is None or ClientConfig is None or ConfigParam is None:
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
    except Exception as exc:  # pragma: no cover
        logger.error("Failed to fetch Nacos config %s/%s: %s", group, data_id, exc)
        return {}


class Settings(BaseSettings):
    """应用配置"""
    DB_HOST: str
    DB_PORT: int
    DB_USER: str
    DB_PASSWORD: str
    DB_NAME: str
    # Milvus settings
    MILVUS_HOST: str = os.getenv("MILVUS_HOST", "localhost")
    MILVUS_PORT: int = int(os.getenv("MILVUS_PORT", "19530"))
    MILVUS_USER: str = os.getenv("MILVUS_USER", "")
    MILVUS_PASSWORD: str = os.getenv("MILVUS_PASSWORD", "")
    MILVUS_DB_NAME: str = os.getenv("MILVUS_DB_NAME", "default")

    # LlamaParse配置
    LLAMA_PARSE_API_KEY: str

    # LLM配置 - 统一的模型配置
    LLM_API_KEY: str = os.getenv("LLM_API_KEY", "")
    LLM_API_BASE: str = os.getenv("LLM_API_BASE", "https://api.openai.com/v1")
    LLM_MODEL_NAME: str = os.getenv("LLM_MODEL_NAME", "gpt-4o")

    # Embedding模型配置
    EMBEDDING_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    EMBEDDING_API_BASE: str = os.getenv("OPENAI_API_BASE", "https://api.openai.com/v1")
    EMBEDDING_MODEL: str = "text-embedding-3-small"
    FILE_PROCESS_CALLBACK_URL: str = os.getenv("FILE_PROCESS_CALLBACK_URL", "")
    FILE_PROCESS_CALLBACK_API_KEY: str = os.getenv("FILE_PROCESS_CALLBACK_API_KEY", "")

    # MinIO / S3 compatible storage
    MINIO_ENDPOINT: str = os.getenv("MINIO_ENDPOINT", "")
    MINIO_ACCESS_KEY: str = os.getenv("MINIO_ACCESS_KEY", "")
    MINIO_SECRET_KEY: str = os.getenv("MINIO_SECRET_KEY", "")
    MINIO_SECURE: bool = os.getenv("MINIO_SECURE", "false").lower() == "true"

    # SerpAPI配置
    SERPAPI_API_KEY: str = os.getenv("SERPAPI_API_KEY", "")

    # Service settings
    SERVICE_NAME: str = os.getenv("SERVICE_NAME", "readify-agi")
    SERVICE_HOST: str = os.getenv("SERVICE_HOST", "")
    SERVICE_PORT: int = int(os.getenv("SERVICE_PORT", "8081"))

    # Nacos settings
    NACOS_ENABLED: bool = False
    NACOS_SERVER_ADDR: str = os.getenv("NACOS_SERVER_ADDR", "127.0.0.1:8848")
    NACOS_NAMESPACE: str = os.getenv("NACOS_NAMESPACE", "")
    NACOS_GROUP: str = os.getenv("NACOS_GROUP", "DEFAULT_GROUP")
    NACOS_USERNAME: str = os.getenv("NACOS_USERNAME", "nacos")
    NACOS_PASSWORD: str = os.getenv("NACOS_PASSWORD", "nacos")
    NACOS_CLUSTER: str = os.getenv("NACOS_CLUSTER", "DEFAULT")
    NACOS_HEARTBEAT_INTERVAL: int = int(os.getenv("NACOS_HEARTBEAT_INTERVAL", "5"))
    NACOS_CONFIG_DATA_ID: str = os.getenv("NACOS_CONFIG_DATA_ID", "")

    # Service discovery settings
    READIFY_SERVER_SERVICE_NAME: str = os.getenv("READIFY_SERVER_SERVICE_NAME", "")

    @property
    def DATABASE_URL(self) -> str:
        return (
            f"mysql+aiomysql://{self.DB_USER}:{self.DB_PASSWORD}@"
            f"{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
            "?charset=utf8mb4&use_unicode=1"
            "&auth_plugin=caching_sha2_password"
        )

    class Config:
        env_file = ".env"
        case_sensitive = True

_nacos_enabled = os.getenv("NACOS_ENABLED", "false").lower() == "true"
_nacos_config = _load_nacos_config() if _nacos_enabled else {}
if _nacos_enabled:
    if not _nacos_config:
        raise RuntimeError(
            "NACOS_ENABLED=true 但未能从 Nacos 拉取到配置，请检查 "
            "NACOS_CONFIG_DATA_ID、NACOS_GROUP、NACOS_NAMESPACE、"
            "NACOS_USERNAME、NACOS_PASSWORD 等环境变量或 Nacos 配置是否正确"
        )
    # 兼容 Nacos 中将某些字段配置为 null 的情况（例如 MILVUS_USER / MILVUS_PASSWORD）
    for _key in ("MILVUS_USER", "MILVUS_PASSWORD"):
        if _key in _nacos_config and _nacos_config[_key] is None:
            _nacos_config[_key] = ""
    settings = Settings(**_nacos_config)
else:
    settings = Settings()
