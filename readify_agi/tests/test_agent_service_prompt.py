import pytest
from pydantic import BaseModel

from app.services.agent_service import AgentService


class DummyArgsSchema(BaseModel):
    query: str


class DummyTool:
    name = "search_files_tool"
    description = "在项目文件中执行语义搜索"
    args_schema = DummyArgsSchema


def test_build_system_prompt_uses_template_placeholder_without_fallback_append():
    agent = AgentService(project_id=1)
    agent.tools = [DummyTool()]
    agent.system_prompt = "你是项目助手。\n工具如下：\n{available_tools}"

    result = agent._build_system_prompt_for_tool_calling()

    assert result == agent.system_prompt
    assert result.count("{available_tools}") == 1
    assert "下面是当前真实可用的工具列表。" not in result


def test_build_system_prompt_raises_when_placeholder_missing():
    agent = AgentService(project_id=1)
    agent.tools = [DummyTool()]
    agent.system_prompt = "你是项目助手。"

    with pytest.raises(ValueError, match=r"\{available_tools\}"):
        agent._build_system_prompt_for_tool_calling()


def test_build_system_prompt_raises_when_system_prompt_missing():
    agent = AgentService(project_id=1)
    agent.tools = [DummyTool()]
    agent.system_prompt = None

    with pytest.raises(ValueError, match=r"\{available_tools\}"):
        agent._build_system_prompt_for_tool_calling()
