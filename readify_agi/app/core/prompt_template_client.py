"""
Prompt Template Client — 从 readify_eval API 获取提示词模板并缓存到内存
懒加载模式：首次获取模板时才通过 Nacos 服务发现定位 eval 服务并拉取模板
"""
import logging
import re
from typing import Dict, Optional

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)

_client_instance: Optional["PromptTemplateClient"] = None


def _convert_eval_to_langchain(text: str) -> str:
    """将 eval 的 <$variable> 格式转换为 LangChain 的 {variable} 格式"""
    return re.sub(r'<\$([a-zA-Z_][a-zA-Z0-9_]*)>', r'{\1}', text)


async def _resolve_eval_base_url() -> str:
    """通过 Nacos 服务发现获取 readify-eval 的基础 URL"""
    from app.core.nacos_client import get_service_discovery

    discovery = await get_service_discovery()
    if discovery is None:
        raise RuntimeError(
            "Nacos 服务发现不可用，无法定位 readify-eval 服务。"
            "请确认 NACOS_ENABLED=true 且 Nacos 配置正确"
        )

    service_name = settings.READIFY_EVAL_SERVICE_NAME
    url = await discovery.get_service_url(service_name)
    if not url:
        raise RuntimeError(
            f"未从 Nacos 发现服务 '{service_name}' 的可用实例，"
            "请确认 readify-eval 已启动并注册到 Nacos"
        )

    logger.info("通过 Nacos 服务发现获取到 readify-eval 地址: %s", url)
    return url


class PromptTemplateClient:
    """
    提示词模板客户端，懒加载模式。
    首次调用 get_template 时才通过 Nacos 服务发现定位 eval 服务并批量拉取模板到内存。
    """

    def __init__(self):
        self._cache: Dict[str, str] = {}
        self._initialized = False

    async def _ensure_initialized(self) -> None:
        """确保模板已加载，未加载则通过服务发现拉取"""
        if self._initialized:
            return

        base_url = await _resolve_eval_base_url()

        url = f"{base_url}/api/v1/prompt-templates/all"
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.get(url)
                resp.raise_for_status()
                data = resp.json()

            items = data.get("items", [])
            for item in items:
                code = item.get("template_code")
                user_prompt = item.get("user_prompt")
                if code and user_prompt:
                    self._cache[code] = _convert_eval_to_langchain(user_prompt)

            logger.info(
                "已从 eval API (%s) 加载 %d 个提示词模板",
                url,
                len(self._cache),
            )
        except Exception as exc:
            raise RuntimeError(
                f"无法从 eval API 获取模板: {exc}"
            ) from exc

        self._initialized = True

    async def get_template(self, code: str) -> str:
        """
        从内存缓存中获取模板内容，首次调用时自动从 eval 服务拉取。

        Args:
            code: 模板编码（template_code）

        Returns:
            模板内容字符串

        Raises:
            KeyError: 模板不存在于缓存中
            RuntimeError: 无法连接 eval 服务
        """
        await self._ensure_initialized()
        cached = self._cache.get(code)
        if cached is None:
            raise KeyError(f"提示词模板 '{code}' 不存在于缓存中，请确认 eval 数据库中已创建该 template_code")
        return cached

    async def refresh(self) -> None:
        """重新从 eval API 拉取模板，刷新缓存"""
        self._cache.clear()
        self._initialized = False
        await self._ensure_initialized()


def get_prompt_client() -> "PromptTemplateClient":
    """获取全局单例 PromptTemplateClient"""
    global _client_instance
    if _client_instance is None:
        _client_instance = PromptTemplateClient()
    return _client_instance
