import json
import logging
from typing import Dict, Optional

from langchain_core.language_models import BaseChatModel

from app.core.config import settings

logger = logging.getLogger(__name__)


def _normalize_anthropic_base_url(url: str) -> str:
    """Normalize Anthropic base_url to avoid duplicate /v1/messages suffixes."""
    url = url.rstrip("/")
    if url.endswith("/v1/messages"):
        url = url[:-len("/v1/messages")]
    elif url.endswith("/v1"):
        url = url[:-len("/v1")]
    return url


def _parse_default_headers() -> Dict[str, str]:
    """Parse LLM_DEFAULT_HEADERS JSON config."""
    raw = settings.LLM_DEFAULT_HEADERS.strip()
    if not raw:
        return {}
    try:
        headers = json.loads(raw)
    except json.JSONDecodeError as exc:
        logger.warning("[LLM Factory] Failed to parse LLM_DEFAULT_HEADERS: %s", exc)
        return {}

    if not isinstance(headers, dict):
        logger.warning("[LLM Factory] LLM_DEFAULT_HEADERS must be a JSON object")
        return {}
    return headers


def _merge_model_kwargs(kwargs: Dict) -> Dict:
    """Disable parallel tool calls for OpenAI-compatible providers unless explicitly overridden."""
    merged = dict(kwargs)
    model_kwargs = dict(merged.get("model_kwargs") or {})
    model_kwargs.setdefault("parallel_tool_calls", False)
    merged["model_kwargs"] = model_kwargs
    return merged


def get_default_headers() -> Dict[str, str]:
    return _parse_default_headers()


def create_chat_model(
    temperature: float = 0.7,
    max_tokens: Optional[int] = None,
    **kwargs,
) -> BaseChatModel:
    """Create a chat model based on the configured provider."""
    provider = settings.LLM_PROVIDER.lower()
    default_headers = _parse_default_headers()

    if provider == "anthropic":
        from langchain_anthropic import ChatAnthropic

        build_kwargs = {
            "model": settings.LLM_MODEL_NAME,
            "api_key": settings.LLM_API_KEY,
            "temperature": temperature,
            "max_tokens": max_tokens or 4096,
            **kwargs,
        }
        if settings.LLM_API_BASE and settings.LLM_API_BASE != "https://api.openai.com/v1":
            normalized_url = _normalize_anthropic_base_url(settings.LLM_API_BASE)
            build_kwargs["anthropic_api_url"] = normalized_url
            logger.info(
                "[LLM Factory] Normalized Anthropic base_url: %s -> %s",
                settings.LLM_API_BASE,
                normalized_url,
            )
        if default_headers:
            build_kwargs["default_headers"] = default_headers

        model = ChatAnthropic(**build_kwargs)
        logger.info("[LLM Factory] Created ChatAnthropic model=%s", settings.LLM_MODEL_NAME)
        return model

    from langchain_openai import ChatOpenAI

    build_kwargs = _merge_model_kwargs(kwargs)
    build_kwargs.update(
        {
            "model": settings.LLM_MODEL_NAME,
            "api_key": settings.LLM_API_KEY,
            "base_url": settings.LLM_API_BASE,
            "temperature": temperature,
        }
    )
    if max_tokens is not None:
        build_kwargs["max_tokens"] = max_tokens
    if default_headers:
        build_kwargs["default_headers"] = default_headers

    model = ChatOpenAI(**build_kwargs)
    logger.info(
        "[LLM Factory] Created ChatOpenAI model=%s, base_url=%s, parallel_tool_calls=%s",
        settings.LLM_MODEL_NAME,
        settings.LLM_API_BASE,
        build_kwargs.get("model_kwargs", {}).get("parallel_tool_calls"),
    )
    return model