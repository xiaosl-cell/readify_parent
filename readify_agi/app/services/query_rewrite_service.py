"""
查询改写服务 — 利用LLM结合对话历史将后续问题改写为独立的搜索查询

提示词模板从 readify_eval 数据库加载（template_code='query_rewrite'）。
"""
import logging
from typing import Optional, Tuple

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage, SystemMessage

from app.core.config import settings
from app.core.llm_factory import create_chat_model

logger = logging.getLogger(__name__)


class QueryRewriteService:
    """
    查询改写服务，在向量检索前将用户的后续问题改写为独立的搜索查询。
    """

    def __init__(self, temperature: float = 0.0, max_tokens: int = 256):
        self.temperature = temperature
        self.max_tokens = max_tokens
        self._llm: Optional[BaseChatModel] = None
        self._system_prompt: Optional[str] = None
        self._user_prompt_template: Optional[str] = None
        self._loaded = False

    def _get_llm(self) -> BaseChatModel:
        if self._llm is None:
            self._llm = create_chat_model(
                temperature=self.temperature,
                max_tokens=self.max_tokens,
            )
        return self._llm

    async def _load_prompts(self) -> Tuple[Optional[str], str]:
        """
        从 eval 数据库加载查询改写提示词模板（system_prompt + user_prompt）。

        Returns:
            (system_prompt, user_prompt_template) 元组

        Raises:
            RuntimeError: 无法从 eval 加载模板
        """
        if self._loaded:
            return self._system_prompt, self._user_prompt_template

        from app.core.prompt_template_client import get_prompt_client
        client = get_prompt_client()
        self._user_prompt_template = await client.get_template("query_rewrite")
        self._system_prompt = await client.get_system_prompt("query_rewrite")
        self._loaded = True
        logger.info("[QueryRewrite] 成功从 eval 数据库加载提示词模板 (system_prompt=%s)",
                    "有" if self._system_prompt else "无")
        return self._system_prompt, self._user_prompt_template

    async def rewrite(self, query: str, conversation_history: str) -> str:
        """
        根据对话历史将查询改写为独立的搜索查询。

        Args:
            query: 原始搜索查询
            conversation_history: 格式化的对话历史文本

        Returns:
            改写后的查询字符串；失败时返回原始查询
        """
        if not conversation_history or not conversation_history.strip():
            logger.debug("[QueryRewrite] 无对话历史，跳过改写")
            return query

        try:
            system_prompt, user_template = await self._load_prompts()
            user_text = user_template.format(history=conversation_history, query=query)
        except Exception as e:
            logger.warning("[QueryRewrite] 模板格式化失败: %s，使用原始查询", str(e))
            return query

        llm = self._get_llm()
        messages = []
        if system_prompt:
            messages.append(SystemMessage(content=system_prompt))
        messages.append(HumanMessage(content=user_text))

        try:
            response = await llm.ainvoke(messages)
            rewritten = response.content.strip()
            if not rewritten:
                logger.warning("[QueryRewrite] LLM 返回空结果，使用原始查询")
                return query
            logger.info("[QueryRewrite] 改写: '%s' -> '%s'", query, rewritten)
            return rewritten
        except Exception as e:
            logger.error("[QueryRewrite] LLM 调用失败: %s，使用原始查询", str(e))
            return query
