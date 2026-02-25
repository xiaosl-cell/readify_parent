"""
LLM 工厂模块 — 根据 LLM_PROVIDER 配置创建对应的 LangChain ChatModel 实例。

支持的 provider：
- "openai"    → ChatOpenAI（兼容所有 OpenAI API 格式的服务）
- "anthropic" → ChatAnthropic（Anthropic Claude 系列模型）
"""
import json
import logging
from typing import Dict, Optional

from langchain_core.language_models import BaseChatModel

from app.core.config import settings

logger = logging.getLogger(__name__)


def _normalize_anthropic_base_url(url: str) -> str:
    """
    规范化 Anthropic API 的 base_url。

    Anthropic SDK 会在 base_url 后自动追加 /v1/messages，
    因此需要从用户配置的 URL 中移除可能包含的 /v1/messages 或 /v1 后缀，
    避免路径重复（如 /v1/v1/messages）。

    示例:
        https://example.com/proxy/v1/messages → https://example.com/proxy
        https://example.com/proxy/v1          → https://example.com/proxy
        https://example.com/proxy             → https://example.com/proxy（不变）
    """
    url = url.rstrip('/')
    if url.endswith('/v1/messages'):
        url = url[:-len('/v1/messages')]
    elif url.endswith('/v1'):
        url = url[:-len('/v1')]
    return url


def _parse_default_headers() -> Dict[str, str]:
    """解析 LLM_DEFAULT_HEADERS 配置，返回 headers 字典。"""
    raw = settings.LLM_DEFAULT_HEADERS.strip()
    if not raw:
        return {}
    try:
        headers = json.loads(raw)
        if isinstance(headers, dict):
            return headers
        logger.warning("[LLM Factory] LLM_DEFAULT_HEADERS 不是合法的 JSON 对象，已忽略")
        return {}
    except json.JSONDecodeError as e:
        logger.warning("[LLM Factory] LLM_DEFAULT_HEADERS JSON 解析失败: %s，已忽略", e)
        return {}


def get_default_headers() -> Dict[str, str]:
    """公开方法，供 Agently 等外部模块获取自定义 headers。"""
    return _parse_default_headers()


def create_chat_model(
    temperature: float = 0.7,
    max_tokens: Optional[int] = None,
    **kwargs,
) -> BaseChatModel:
    """
    根据 settings.LLM_PROVIDER 创建对应的 ChatModel 实例。

    Args:
        temperature: 采样温度
        max_tokens: 最大输出 token 数（Anthropic 要求必须指定，默认 4096）
        **kwargs: 传递给底层 ChatModel 的额外参数

    Returns:
        BaseChatModel 实例
    """
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
            # Anthropic SDK 会自动在 base_url 后追加 /v1/messages，
            # 需要规范化以避免 /v1/v1/messages 等路径重复问题。
            # 使用 anthropic_api_url 参数名以兼容 langchain-anthropic 所有版本（0.1.0+）
            normalized_url = _normalize_anthropic_base_url(settings.LLM_API_BASE)
            build_kwargs["anthropic_api_url"] = normalized_url
            logger.info("[LLM Factory] Anthropic base_url 规范化: %s -> %s",
                        settings.LLM_API_BASE, normalized_url)
        if default_headers:
            build_kwargs["default_headers"] = default_headers

        model = ChatAnthropic(**build_kwargs)
        logger.info("[LLM Factory] 创建 ChatAnthropic 实例, model=%s", settings.LLM_MODEL_NAME)
        return model

    # 默认使用 OpenAI
    from langchain_openai import ChatOpenAI

    build_kwargs = {
        "model": settings.LLM_MODEL_NAME,
        "api_key": settings.LLM_API_KEY,
        "base_url": settings.LLM_API_BASE,
        "temperature": temperature,
        **kwargs,
    }
    if max_tokens is not None:
        build_kwargs["max_tokens"] = max_tokens
    if default_headers:
        build_kwargs["default_headers"] = default_headers

    model = ChatOpenAI(**build_kwargs)
    logger.info("[LLM Factory] 创建 ChatOpenAI 实例, model=%s, base_url=%s",
                settings.LLM_MODEL_NAME, settings.LLM_API_BASE)
    return model
