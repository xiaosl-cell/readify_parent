import asyncio
import logging
import os
import time
from typing import Any, Dict

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

# Load .env before Settings is instantiated so NACOS_* flags are available.
load_dotenv()


def _default_embedding_api_key() -> str:
    explicit_key = os.getenv("EMBEDDING_API_KEY", "")
    if explicit_key:
        return explicit_key

    hunyuan_key = os.getenv("HUNYUAN_API_KEY", "")
    if hunyuan_key:
        return hunyuan_key

    llm_base = os.getenv("LLM_API_BASE", "")
    if "hunyuan.cloud.tencent.com" in llm_base:
        return os.getenv("LLM_API_KEY", "")

    return ""


def _load_nacos_config() -> Dict[str, Any]:
    """Optionally pull configuration from Nacos Config and return it as a dict."""
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
        logger.warning("Nacos config not loaded because nacos-sdk-python or PyYAML is missing")
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

    for attempt in range(1, 4):
        try:
            result = asyncio.run(_pull())
            if result:
                return result
            logger.warning("Nacos config %s/%s returned empty, attempt %d/3", group, data_id, attempt)
        except Exception as exc:  # pragma: no cover
            logger.warning(
                "Failed to fetch Nacos config %s/%s (attempt %d/3): %s",
                group,
                data_id,
                attempt,
                exc,
            )
        if attempt < 3:
            time.sleep(2)

    logger.error("All 3 attempts to fetch Nacos config %s/%s failed", group, data_id)
    return {}


class Settings(BaseSettings):
    """Application settings."""

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

    # LlamaParse settings
    LLAMA_PARSE_API_KEY: str = os.getenv("LLAMA_PARSE_API_KEY", "")

    # Parser / OCR settings
    PARSER_PROVIDER: str = os.getenv("PARSER_PROVIDER", "local")
    OCR_BASE_URL: str = os.getenv("OCR_BASE_URL", "http://localhost:8090")
    OCR_LANG: str = os.getenv("OCR_LANG", "ch")
    OCR_TIMEOUT_SEC: int = int(os.getenv("OCR_TIMEOUT_SEC", "120"))
    TENCENT_SECRET_ID: str = os.getenv("TENCENT_SECRET_ID", "")
    TENCENT_SECRET_KEY: str = os.getenv("TENCENT_SECRET_KEY", "")
    TENCENT_OCR_REGION: str = os.getenv("TENCENT_OCR_REGION", "ap-guangzhou")

    # LLM settings
    LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "openai")
    LLM_API_KEY: str = os.getenv("LLM_API_KEY", "")
    LLM_API_BASE: str = os.getenv("LLM_API_BASE", "https://api.openai.com/v1")
    LLM_MODEL_NAME: str = os.getenv("LLM_MODEL_NAME", "gpt-4o")
    LLM_DEFAULT_HEADERS: str = os.getenv("LLM_DEFAULT_HEADERS", "")

    # Query rewrite settings
    QUERY_REWRITE_ENABLED: bool = os.getenv("QUERY_REWRITE_ENABLED", "true").lower() == "true"

    # Embedding settings. Default to Tencent Hunyuan's OpenAI-compatible embeddings endpoint.
    EMBEDDING_API_KEY: str = _default_embedding_api_key()
    EMBEDDING_API_BASE: str = os.getenv(
        "EMBEDDING_API_BASE",
        os.getenv("HUNYUAN_API_BASE", "https://api.hunyuan.cloud.tencent.com/v1"),
    )
    EMBEDDING_MODEL: str = os.getenv("EMBEDDING_MODEL", "hunyuan-embedding")
    EMBEDDING_REQUEST_BATCH_SIZE: int = int(os.getenv("EMBEDDING_REQUEST_BATCH_SIZE", "50"))
    EMBEDDING_COLLECTION_NAME: str = os.getenv("EMBEDDING_COLLECTION_NAME", "rf_documents")

    FILE_PROCESS_CALLBACK_URL: str = os.getenv("FILE_PROCESS_CALLBACK_URL", "")
    FILE_PROCESS_CALLBACK_API_KEY: str = os.getenv("FILE_PROCESS_CALLBACK_API_KEY", "")

    # MinIO / S3 compatible storage
    MINIO_ENDPOINT: str = os.getenv("MINIO_ENDPOINT", "")
    MINIO_ACCESS_KEY: str = os.getenv("MINIO_ACCESS_KEY", "")
    MINIO_SECRET_KEY: str = os.getenv("MINIO_SECRET_KEY", "")
    MINIO_SECURE: bool = os.getenv("MINIO_SECURE", "false").lower() == "true"

    # SerpAPI settings
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

    # Service discovery
    READIFY_SERVER_SERVICE_NAME: str = os.getenv("READIFY_SERVER_SERVICE_NAME", "")
    READIFY_EVAL_SERVICE_NAME: str = os.getenv("READIFY_EVAL_SERVICE_NAME", "readify-eval")
    READIFY_EVAL_BASE_URL: str = os.getenv("READIFY_EVAL_BASE_URL", "")

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
            "NACOS_ENABLED=true but no config was loaded from Nacos. Check "
            "NACOS_CONFIG_DATA_ID, NACOS_GROUP, NACOS_NAMESPACE, "
            "NACOS_USERNAME, NACOS_PASSWORD, and the remote Nacos config."
        )
    for key in ("MILVUS_USER", "MILVUS_PASSWORD"):
        if key in _nacos_config and _nacos_config[key] is None:
            _nacos_config[key] = ""
    settings = Settings(**_nacos_config)
else:
    settings = Settings()
