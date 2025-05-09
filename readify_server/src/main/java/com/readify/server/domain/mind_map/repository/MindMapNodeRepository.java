package com.readify.server.domain.mind_map.repository;

import com.readify.server.domain.mind_map.model.MindMapNode;

import java.util.List;
import java.util.Optional;

public interface MindMapNodeRepository {
    /**
     * 保存节点
     *
     * @param node 节点信息
     * @return 保存后的节点
     */
    MindMapNode save(MindMapNode node);

    /**
     * 批量保存节点
     *
     * @param nodes 节点列表
     * @return 保存后的节点列表
     */
    List<MindMapNode> batchSave(List<MindMapNode> nodes);

    /**
     * 根据ID查找节点
     *
     * @param id 节点ID
     * @return 节点信息
     */
    Optional<MindMapNode> findById(Long id);

    /**
     * 根据文件ID查找所有节点
     *
     * @param fileId 文件ID
     * @return 节点列表
     */
    List<MindMapNode> findByFileId(Long fileId);

    /**
     * 根据思维导图ID查找所有节点
     *
     * @param mindMapId 思维导图ID
     * @return 节点列表
     */
    List<MindMapNode> findByMindMapId(Long mindMapId);

    /**
     * 根据父节点ID查找所有子节点
     *
     * @param parentId 父节点ID
     * @return 子节点列表
     */
    List<MindMapNode> findByParentId(Long parentId);

    /**
     * 根据文件ID查找根节点
     *
     * @param fileId 文件ID
     * @return 根节点
     */
    Optional<MindMapNode> findRootNodeByFileId(Long fileId);

    /**
     * 根据思维导图ID查找根节点
     *
     * @param mindMapId 思维导图ID
     * @return 根节点
     */
    Optional<MindMapNode> findRootNodeByMindMapId(Long mindMapId);

    /**
     * 根据ID删除节点
     *
     * @param id 节点ID
     * @return 是否删除成功
     */
    boolean deleteById(Long id);

    /**
     * 根据文件ID删除所有节点
     *
     * @param fileId 文件ID
     * @return 删除的节点数量
     */
    int deleteByFileId(Long fileId);

    /**
     * 根据思维导图ID删除所有节点
     *
     * @param mindMapId 思维导图ID
     * @return 删除的节点数量
     */
    int deleteByMindMapId(Long mindMapId);

    /**
     * 更新节点序列号
     *
     * @param id 节点ID
     * @param sequence 新的序列号
     * @return 是否更新成功
     */
    boolean updateSequence(Long id, Integer sequence);
} 