import json
import logging
import os
from typing import Dict, Any, List, Literal

import Agently
import dotenv
import httpx
from pydantic import BaseModel, Field

from app.core.config import settings
from app.core.llm_factory import get_default_headers
from ..utils.OutputParser import parse_to_type

logger = logging.getLogger(__name__)


def _patch_agently_claude_headers(custom_headers: Dict[str, str]):
    """
    Monkey-patch Agently Claude 插件的 request_model 方法以注入自定义 HTTP headers。
    Agently Claude 插件（Agently/plugins/request/Claude.py）硬编码了 headers，
    不支持通过 settings 配置，因此需要 patch。
    """
    from Agently.plugins.request.Claude import Claude

    _orig_request_model = Claude.request_model

    async def _patched_request_model(self, request_data: dict):
        api_key = self.model_settings.get_trace_back("auth.api_key")
        base_url = self.model_settings.get_trace_back("url", "https://api.anthropic.com/v1")
        if base_url.endswith("/"):
            base_url = base_url[:-1]
        proxy = self.request.settings.get_trace_back("proxy")
        messages = request_data["messages"]
        system_prompt = ""
        request_messages = []
        for message in messages:
            if message["role"] == "system":
                system_prompt += f"{message['content'][0]['text']}\n"
            else:
                request_messages.append(message)
        options = request_data["options"]
        if system_prompt != "":
            options.update({"system": system_prompt})
        for key, value in self.default_options.items():
            if key not in options:
                options.update({key: value})
        headers = {
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        }
        headers.update(custom_headers)
        request_params = {
            "headers": headers,
            "data": json.dumps({"messages": request_messages, **options}),
            "timeout": None,
        }
        client_params = {}
        if proxy:
            client_params["proxy"] = proxy
        async with httpx.AsyncClient(**client_params) as client:
            async with client.stream(
                "POST",
                f"{base_url}/messages",
                **request_params
            ) as response:
                async for chunk in response.aiter_lines():
                    yield chunk

    Claude.request_model = _patched_request_model
    logger.info("[TextWorkflow] 已 patch Agently Claude 插件以注入自定义 headers")


class CheckFormat(BaseModel):
    type: str = Field(..., description="问题类型")
    description: str = Field(description="问题描述，需包含具体上下文信息如：")

    def __str__(self):
        return json.dumps(self.model_dump())

class ListCheckFormat(BaseModel):
    issues: List[CheckFormat] = Field(description="问题列表")

class FixFormat(BaseModel):
    origin_text: str = Field(description="原始文本")
    fixed_text: str = Field(description="修复后的文本")

    def __str__(self):
        return json.dumps(self.model_dump())


class TextWorkflowService:
    def __init__(self):
        dotenv.load_dotenv()

        provider = settings.LLM_PROVIDER.lower()
        api_key = settings.LLM_API_KEY

        # 创建 agent 工厂并根据 provider 配置
        custom_headers = get_default_headers()
        if provider == "anthropic":
            # Agently Claude 插件不支持自定义 headers，需要 monkey-patch
            if custom_headers:
                _patch_agently_claude_headers(custom_headers)
            self.agent_factory = (
                Agently.AgentFactory()
                .set_settings("current_model", "Claude")
                .set_settings("model.Claude.auth", {"api_key": api_key})
                .set_settings("model.Claude.options", {"model": settings.LLM_MODEL_NAME})
            )
            # 如果配置了自定义 API 地址且不是默认 OpenAI 地址，则设置
            if settings.LLM_API_BASE and settings.LLM_API_BASE != "https://api.openai.com/v1":
                self.agent_factory.set_settings("model.Claude.url", settings.LLM_API_BASE)
        else:
            self.agent_factory = (
                Agently.AgentFactory()
                .set_settings("current_model", "OpenAI")
                .set_settings("model.OpenAI.model", settings.LLM_MODEL_NAME)
                .set_settings("model.OpenAI.auth", {"api_key": api_key})
                .set_settings("model.OpenAI.temperature", 0.5)
            )
            # 如果配置了自定义 API 地址，则设置
            if settings.LLM_API_BASE and settings.LLM_API_BASE != "https://api.openai.com/v1":
                self.agent_factory.set_settings("model.OpenAI.url", settings.LLM_API_BASE)
            # 注入自定义 headers（通过自定义 httpx 客户端）
            if custom_headers:
                self.agent_factory.set_settings(
                    "model.OpenAI.httpx_client",
                    httpx.AsyncClient(headers=custom_headers),
                )
        
        # 创建工作流
        self.workflow = Agently.Workflow()
        self._setup_workflows()

    def _setup_workflows(self):
        # 检查工作块
        @self.workflow.chunk()
        def check_format(inputs, storage):

            check_format_agent = self.agent_factory.create_agent("check_format")
            check_format_agent.set_agent_prompt("role", "你是一个专业的文本格式检查员,专业核对被机器学习识别出的文本错误")
            check_format_agent.set_agent_prompt("rule", """严格检查以下问题类型：
1. 【乱码】出现#￥%&等无意义符号（数学符号/公式除外）
2. 【错别字】发音相近但语义不符（需指明正确写法，如'平果->苹果'）
3. 【文字顺序错误】语序明显错误（如'好你->你好'）
4. 【双栏结构】明显存在并行文本段（需标注分界位置）
5. 【特殊符号错误】温度单位'°C'被识别为'oC'

排除情况：
- 英文缩写（如LLM、CNN等） 
- 专业术语（如BERT、Transformer）
- 数学公式中的特殊符号
- 合理的数字符号（如$20、5%）
                                                """)
            check_format_agent.set_agent_prompt("output", """以纯json数组文本格式输出检查出来的问题：\n[{\"type\":\"问题类型\",\"description\":\"问题描述\"}]""")
            check_format_agent.set_agent_prompt("example", """示例输出：
            [{
              "type": "乱码",
              "description": "句子：xxx中出现乱码：#￥%",
            }]
            请严格按此格式输出""")
            check_result = check_format_agent.input(f"需要检查的文本如下：{storage.get('source_text')}").start()
            issue = parse_to_type("提取以下内容中的描述的问题", check_result, ListCheckFormat)
            print(f"check_format中的issues: {json.dumps([issue.model_dump() for issue in issue.issues], ensure_ascii=False)}")
            storage.set("format_issues", issue.issues)

        # 修复格式
        @self.workflow.chunk()
        def fix_format(inputs, storage):
            fix_format_agent = self.agent_factory.create_agent("fix_format")
            fix_format_agent.set_agent_prompt("role", "你是一个专业的文本格式修复员,专业修复被机器学习识别出的文本问题")
            fix_format_agent.set_agent_prompt("rule", """
                                                    1. 修复文本的问题
                                                    2. 格式化输出修复后的文本
                                                    3. 输出格式为json
                                                    请用严格JSON格式输出，确保：
                                                        - 双栏内容完全分离
                                                        - 保留原始数字和特殊符号（如数学符号）
                                                        - 不合并跨栏语句
                                                        - 空行转换为换行符
                                                    请将左右并排排版的内容按以下规则分割为独立段落：
                                                        1. 分割依据为：
                                                           - 分界线：当出现连续的虚线、竖线或空行时
                                                           - 顺序标记：优先保留原始视觉顺序（左→右）
                                                        2. 保持每个段落完整性，不合并跨栏内容
                                                    **不要丢弃任何正常文本**
                                                """)
            fix_format_agent.set_agent_prompt("output", """直接输出标准的JSON数组格式，不要包含任何Markdown语法或额外说明，fixed_text请直接输出修复后的文本：{"origin_text":"", "fixed_text":""}""")
            fix_result = fix_format_agent.input(f"需要修复的原始文本：{storage.get('source_text')}\n 需要修复的格式问题：{storage.get('format_issues')} ").start()
            fix_result = parse_to_type("提取文本中的source_text和fixed_text", fix_result, FixFormat)
            storage.set("fixed_text", fix_result.fixed_text)

        # 语义分段工作块
        @self.workflow.chunk()
        def split_paragraphs(inputs, storage):
            split_paragraphs_agent = self.agent_factory.create_agent("split_paragraphs")
            split_paragraphs_agent.set_agent_prompt("role", "你是一个专业的文本语义分析员，擅长根据内容主题进行段落划分")
            split_paragraphs_agent.set_agent_prompt("rule", """
                                                    1. 仔细分析文本的语义连贯性，并根据内容主题进行段落划分
                                                    2. 将讨论同一主题、同一事件或具有连续性的内容保持在同一段落
                                                    3. 当出现以下情况时进行分段：
                                                       - 主题发生转换
                                                       - 讨论对象发生变化
                                                       - 时间/空间场景转换
                                                    4. 输出格式为JSON数组，每个元素是一个完整段落
                                                    5. **目录、摘要等特殊段落完整输出，不要分段**
                                                    6. **每个段落不要太小**
                                                """)
            split_paragraphs_agent.set_agent_prompt("output", """请将内容分段处理，直接输出标准的JSON数组格式，不要包含任何Markdown语法或额外说明。示例格式：["段落1完整内容","段落2完整内容"]""")
            paragraphs = split_paragraphs_agent.input(f"需要分段的文本：{storage.get('fixed_text')}").start()
            storage.set("paragraphs", paragraphs)
            return {
                "paragraphs": paragraphs,
                "fixed_text": storage.get("fixed_text"),
                "format_issues": storage.get("format_issues"),
                "source_text": storage.get("source_text")
            }


        # 连接工作流
        (
            self.workflow
            .connect_to("check_format")
            .connect_to("fix_format")
            .connect_to("split_paragraphs")
            .connect_to("end")
        )

    async def text_repair(self, text: str) -> Dict[str, Any]:
        """
        修复文本的完整工作流
        """
        storage={"source_text": text}
        workflow_result = await self.workflow.start_async(storage=storage)
        result = workflow_result.get("default")
        print(f"process_text中的format_issues: {result.get('format_issues')}")
        return {
            "source_text": text,
            "format_issues": [issue.model_dump() for issue in result.get("format_issues", [])] if result.get("format_issues") else [],
            "fixed_text": result.get("fixed_text"),
            "paragraphs": result.get("paragraphs")
        }