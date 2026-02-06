package com.readify.server.domain.mind_map.service;

import com.readify.server.domain.mind_map.model.MindMapNode;
import com.readify.server.domain.mind_map.model.MindMapNodeTree;

import java.util.List;
import java.util.Optional;

public interface MindMapNodeService {
    /**
     * 保存思维导图节点
     *
     * @param node 节点信息
     * @return 保存后的节点
     */
    MindMapNode saveNode(MindMapNode node);

    /**
     * 批量保存思维导图节点
     *
     * @param nodes 节点列表
     * @return 保存后的节点列表
     */
    List<MindMapNode> batchSaveNodes(List<MindMapNode> nodes);

    /**
     * 获取思维导图节点
     *
     * @param id 节点ID
     * @return 节点信息
     */
    MindMapNode getNodeById(Long id);

    /**
     * 获取文件的所有节点
     *
     * @param fileId 文件ID
     * @return 节点列表
     */
    List<MindMapNode> getNodesByFileId(Long fileId);
    
    /**
     * 获取思维导图的所有节点
     *
     * @param mindMapId 思维导图ID
     * @return 节点列表
     */
    List<MindMapNode> getNodesByMindMapId(Long mindMapId);

    /**
     * 获取父节点的子节点
     *
     * @param parentId 父节点ID
     * @return 子节点列表
     */
    List<MindMapNode> getChildrenByParentId(Long parentId);
    
    /**
     * 根据思维导图ID查找根节点
     *
     * @param mindMapId 思维导图ID
     * @return 根节点信息，不存在则返回空
     */
    Optional<MindMapNode> findRootNodeByMindMapId(Long mindMapId);

    /**
     * 删除节点
     *
     * @param id 节点ID
     * @return 是否删除成功
     */
    boolean deleteNode(Long id);

    /**
     * 删除文件的所有节点
     *
     * @param fileId 文件ID
     * @return 删除的节点数量
     */
    int deleteNodesByFileId(Long fileId);
    
    /**
     * 删除思维导图的所有节点
     *
     * @param mindMapId 思维导图ID
     * @return 删除的节点数量
     */
    int deleteNodesByMindMapId(Long mindMapId);

    /**
     * 更新节点序列号
     *
     * @param id 节点ID
     * @param sequence 新的序列号
     * @return 是否更新成功
     */
    boolean updateNodeSequence(Long id, Integer sequence);

    /**
     * 获取完整的思维导图树（使用文件ID）
     *
     * @param fileId 文件ID
     * @return 思维导图树形结构
     */
    MindMapNodeTree getFullMindMapByFileId(Long fileId);
    
    /**
     * 获取完整的思维导图树（使用思维导图ID）
     *
     * @param mindMapId 思维导图ID
     * @return 思维导图树形结构
     */
    MindMapNodeTree getFullMindMap(Long mindMapId, Long userId);
    
    /**
     * 根据节点ID获取以该节点为根的子树
     *
     * @param nodeId 节点ID
     * @return 思维导图子树
     */
    MindMapNodeTree getSubTreeByNodeId(Long nodeId, Long userId);
}
