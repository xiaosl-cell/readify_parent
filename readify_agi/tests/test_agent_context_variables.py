import pytest

from app.services.agent_service import AgentService
from app.services.coordinator_agent_service import CoordinatorAgentService


@pytest.mark.asyncio
async def test_run_builds_full_prompt_context_before_ainvoke():
    agent = AgentService(project_id=1)
    agent.tools = []

    class DummyProjectRepo:
        async def get_project_info(self, project_id):
            return {"name": "Demo", "description": "Desc"}

    class DummyConversationRepo:
        async def create(self, **kwargs):
            return None

    captured = {}

    class DummyExecutor:
        async def ainvoke(self, payload):
            captured.update(payload)
            return {"output": "ok"}

    agent.project_repo = DummyProjectRepo()
    agent.conversation_repo = DummyConversationRepo()
    agent.agent_executor = DummyExecutor()

    async def fake_context(*args, **kwargs):
        return []

    agent._get_conversation_context = fake_context

    result = await agent.run("hello")

    assert result["output"] == "ok"
    assert captured["input"] == "hello"
    assert "available_tools" in captured


@pytest.mark.asyncio
async def test_coordinator_before_generation_includes_available_tools_and_agents():
    agent = CoordinatorAgentService(project_id=1)
    agent.tools = []
    agent.specialized_agents = {"QUESTIONER": object(), "NOTE_AGENT": object()}

    class DummyProjectRepo:
        async def get_project_info(self, project_id):
            return {"name": "Demo", "description": "Desc"}

    async def fake_context(*args, **kwargs):
        return []

    async def fake_callback(_data):
        return None

    agent.project_repo = DummyProjectRepo()
    agent._get_conversation_context = fake_context

    context = await agent._before_generation("hello", fake_callback)

    assert context["input"] == "hello"
    assert "available_tools" in context
    assert context["available_agents"] == "QUESTIONER, NOTE_AGENT"
