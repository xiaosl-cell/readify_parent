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
            build_kwargs["base_url"] = settings.LLM_API_BASE
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
