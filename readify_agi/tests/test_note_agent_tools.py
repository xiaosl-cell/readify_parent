import json

import pytest

from app.services.note_agent_service import NoteAgentService


class DummyDocument:
    id = 1
    file_id = 2
    content = "doc content"
    sequence = 3
    create_time = 111
    update_time = 222


class DummyDocumentRepo:
    async def get_by_id(self, document_id):
        if document_id == 1:
            return DummyDocument()
        return None


class DummyNode:
    def __init__(self, node_id, content, parent_id=10):
        self.id = node_id
        self.content = content
        self.parent_id = parent_id


class DummyMindMapNodeRepo:
    def __init__(self):
        self.updated = None
        self.deleted = None

    async def get_by_id(self, node_id):
        if node_id == 1:
            return DummyNode(1, "old title")
        if node_id == 99:
            return DummyNode(99, "root", parent_id=None)
        return None

    async def update_node_content(self, node_id, content):
        self.updated = {"node_id": node_id, "content": content}
        return DummyNode(node_id, content)

    async def delete_node(self, node_id, delete_descendants=True):
        if node_id == 99:
            raise ValueError("根节点不允许删除")
        self.deleted = {"node_id": node_id, "delete_descendants": delete_descendants}
        return {"deleted_count": 2, "deleted_node_ids": [node_id, 2]}


@pytest.mark.asyncio
async def test_get_document_by_id_returns_document_times():
    agent = NoteAgentService(project_id=1, context={"mind_map_id": 1})
    agent.document_repo = DummyDocumentRepo()

    tools = await agent._load_tools()
    tool = next(item for item in tools if item.name == "get_document_by_id")

    result = await tool.ainvoke('{"document_id": 1}')
    payload = json.loads(result)

    assert payload["id"] == 1
    assert payload["create_time"] == 111
    assert payload["update_time"] == 222
    assert "created_at" not in payload
    assert "updated_at" not in payload


@pytest.mark.asyncio
async def test_update_mind_map_node_updates_content():
    agent = NoteAgentService(project_id=1, context={"mind_map_id": 1})
    agent.mind_map_node_repo = DummyMindMapNodeRepo()

    tools = await agent._load_tools()
    tool = next(item for item in tools if item.name == "update_mind_map_node")

    result = await tool.ainvoke('{"node_id": 1, "content": "RNN（循环神经网络）"}')
    payload = json.loads(result)

    assert payload["success"] is True
    assert payload["node_id"] == 1
    assert payload["old_content"] == "old title"
    assert payload["new_content"] == "RNN（循环神经网络）"


@pytest.mark.asyncio
async def test_delete_mind_map_node_returns_deleted_nodes():
    agent = NoteAgentService(project_id=1, context={"mind_map_id": 1})
    agent.mind_map_node_repo = DummyMindMapNodeRepo()

    tools = await agent._load_tools()
    tool = next(item for item in tools if item.name == "delete_mind_map_node")

    result = await tool.ainvoke('{"node_id": 1, "delete_descendants": true}')
    payload = json.loads(result)

    assert payload["success"] is True
    assert payload["node_id"] == 1
    assert payload["deleted_count"] == 2
    assert payload["deleted_node_ids"] == [1, 2]
