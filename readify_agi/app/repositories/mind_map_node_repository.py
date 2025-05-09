from typing import Optional, List, Dict
import time

from sqlalchemy import select
from sqlalchemy.sql import and_

from app.models.mind_map_node import MindMapNodeDB, MindMapNodeTreeResponse, MindMapNodeCreate
from app.repositories import BaseRepository


class MindMapNodeRepository(BaseRepository):
    """思维导图节点仓储层"""
    
    async def create_node(self, node: MindMapNodeCreate) -> MindMapNodeDB:
        """创建思维导图节点
        
        Args:
            node: 节点创建模型
            
        Returns:
            创建的思维导图节点对象
        """
        try:
            db = await self._ensure_session()
            now = int(time.time())
            db_node = MindMapNodeDB(
                **node.model_dump(),
                created_time=now,
                updated_time=now
            )
            db.add(db_node)
            await db.commit()
            await db.refresh(db_node)
            return db_node
        finally:
            await self._cleanup_session()
            
    async def get_by_id(self, node_id: int) -> Optional[MindMapNodeDB]:
        """根据ID获取思维导图节点
        
        Args:
            node_id: 节点ID
            
        Returns:
            思维导图节点对象，如果不存在则返回None
        """
        try:
            db = await self._ensure_session()
            query = select(MindMapNodeDB).where(
                and_(
                    MindMapNodeDB.id == node_id,
                    MindMapNodeDB.deleted == False
                )
            )
            result = await db.execute(query)
            return result.scalar_one_or_none()
        finally:
            await self._cleanup_session()
            
    async def get_nodes_by_mind_map_id(self, mind_map_id: int) -> List[MindMapNodeDB]:
        """获取思维导图下的所有节点
        
        Args:
            mind_map_id: 思维导图ID
            
        Returns:
            节点列表
        """
        try:
            db = await self._ensure_session()
            query = select(MindMapNodeDB).where(
                and_(
                    MindMapNodeDB.mind_map_id == mind_map_id,
                    MindMapNodeDB.deleted == False
                )
            ).order_by(MindMapNodeDB.level, MindMapNodeDB.sequence)
            result = await db.execute(query)
            return result.scalars().all()
        finally:
            await self._cleanup_session()
            
    async def get_mind_map_tree(self, mind_map_id: int) -> MindMapNodeTreeResponse:
        """获取完整的思维导图树形结构
        
        Args:
            mind_map_id: 思维导图ID
            
        Returns:
            树形结构的思维导图
        """
        # 获取所有节点
        nodes = await self.get_nodes_by_mind_map_id(mind_map_id)
        if not nodes:
            return None
            
        # 将节点列表转换为字典，方便查找
        node_dict: Dict[int, MindMapNodeDB] = {node.id: node for node in nodes}
        
        # 找出根节点
        root_nodes = [node for node in nodes if node.parent_id is None]
        if not root_nodes:
            return None
        
        # 构建树形结构
        root_node = root_nodes[0]  # 取第一个根节点，通常思维导图只有一个根节点
        tree = self._build_tree_recursively(root_node, node_dict)
        
        return tree
        
    def _build_tree_recursively(self, node: MindMapNodeDB, node_dict: Dict[int, MindMapNodeDB]) -> MindMapNodeTreeResponse:
        """递归构建树形结构
        
        Args:
            node: 当前节点
            node_dict: 节点字典
            
        Returns:
            树形结构的节点
        """
        # 创建当前节点的响应对象
        tree_node = MindMapNodeTreeResponse(
            id=node.id,
            project_id=node.project_id,
            mind_map_id=node.mind_map_id,
            file_id=node.file_id,
            parent_id=node.parent_id,
            content=node.content,
            sequence=node.sequence,
            level=node.level,
            created_time=node.created_time,
            updated_time=node.updated_time,
            children=[]
        )
        
        # 查找当前节点的所有子节点
        child_nodes = [n for n in node_dict.values() if n.parent_id == node.id]
        
        # 按顺序排序子节点
        child_nodes.sort(key=lambda x: x.sequence)
        
        # 递归处理子节点
        for child in child_nodes:
            child_tree = self._build_tree_recursively(child, node_dict)
            tree_node.children.append(child_tree)
            
        return tree_node 