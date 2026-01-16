package com.readify.server.domain.mind_map.service.impl;

import com.readify.server.domain.mind_map.model.MindMapNode;
import com.readify.server.domain.mind_map.model.MindMapNodeTree;
import com.readify.server.domain.mind_map.repository.MindMapNodeRepository;
import com.readify.server.domain.mind_map.service.MindMapNodeService;
import com.readify.server.infrastructure.common.exception.NotFoundException;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;

import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.stream.Collectors;

@Service
@RequiredArgsConstructor
public class MindMapNodeServiceImpl implements MindMapNodeService {
    private final MindMapNodeRepository mindMapNodeRepository;

    @Override
    public MindMapNode saveNode(MindMapNode node) {
        return mindMapNodeRepository.save(node);
    }

    @Override
    public List<MindMapNode> batchSaveNodes(List<MindMapNode> nodes) {
        return mindMapNodeRepository.batchSave(nodes);
    }

    @Override
    public MindMapNode getNodeById(Long id) {
        return mindMapNodeRepository.findById(id)
                .orElseThrow(() -> new NotFoundException("思维导图节点不存在"));
    }

    @Override
    public List<MindMapNode> getNodesByFileId(Long fileId) {
        return mindMapNodeRepository.findByFileId(fileId);
    }

    @Override
    public List<MindMapNode> getNodesByMindMapId(Long mindMapId) {
        return mindMapNodeRepository.findByMindMapId(mindMapId);
    }

    @Override
    public List<MindMapNode> getChildrenByParentId(Long parentId) {
        return mindMapNodeRepository.findByParentId(parentId);
    }

    @Override
    public Optional<MindMapNode> findRootNodeByMindMapId(Long mindMapId) {
        return mindMapNodeRepository.findRootNodeByMindMapId(mindMapId);
    }

    @Override
    public boolean deleteNode(Long id) {
        return mindMapNodeRepository.deleteById(id);
    }

    @Override
    public int deleteNodesByFileId(Long fileId) {
        return mindMapNodeRepository.deleteByFileId(fileId);
    }

    @Override
    public int deleteNodesByMindMapId(Long mindMapId) {
        return mindMapNodeRepository.deleteByMindMapId(mindMapId);
    }

    @Override
    public boolean updateNodeSequence(Long id, Integer sequence) {
        return mindMapNodeRepository.updateSequence(id, sequence);
    }

    @Override
    public MindMapNodeTree getFullMindMapByFileId(Long fileId) {
        // 查找根节点
        MindMapNode rootNode = mindMapNodeRepository.findRootNodeByFileId(fileId)
                .orElseThrow(() -> new NotFoundException("思维导图根节点不存在"));

        // 获取所有节点
        List<MindMapNode> allNodes = mindMapNodeRepository.findByFileId(fileId);

        // 构建树形结构
        return buildMindMapTree(rootNode, allNodes);
    }

    @Override
    public MindMapNodeTree getFullMindMap(Long mindMapId) {
        // 查找根节点
        MindMapNode rootNode = mindMapNodeRepository.findRootNodeByMindMapId(mindMapId)
                .orElseThrow(() -> new NotFoundException("思维导图根节点不存在"));

        // 获取所有节点
        List<MindMapNode> allNodes = mindMapNodeRepository.findByMindMapId(mindMapId);

        // 构建树形结构
        return buildMindMapTree(rootNode, allNodes);
    }

    @Override
    public MindMapNodeTree getSubTreeByNodeId(Long nodeId) {
        // 查找指定节点
        MindMapNode node = mindMapNodeRepository.findById(nodeId)
                .orElseThrow(() -> new NotFoundException("思维导图节点不存在"));

        // 获取所有节点，优先使用思维导图ID查询
        List<MindMapNode> allNodes;
        if (node.getMindMapId() != null) {
            allNodes = mindMapNodeRepository.findByMindMapId(node.getMindMapId());
        } else {
            allNodes = mindMapNodeRepository.findByFileId(node.getFileId());
        }

        // 构建树形结构
        return buildMindMapTree(node, allNodes);
    }

    /**
     * 构建思维导图树形结构
     *
     * @param rootNode 根节点
     * @param allNodes 所有节点
     * @return 树形结构
     */
    private MindMapNodeTree buildMindMapTree(MindMapNode rootNode, List<MindMapNode> allNodes) {
        // 创建根节点树
        MindMapNodeTree rootTree = MindMapNodeTree.fromMindMapNode(rootNode);

        // 按父节点ID对节点进行分组
        Map<Long, List<MindMapNode>> nodesByParentId = allNodes.stream()
                .filter(node -> node.getParentId() != null) // 过滤掉根节点
                .collect(Collectors.groupingBy(MindMapNode::getParentId));

        // 递归构建树形结构
        buildChildren(rootTree, nodesByParentId);

        return rootTree;
    }

    /**
     * 递归构建子节点
     *
     * @param parentTree      父节点树
     * @param nodesByParentId 按父节点ID分组的节点Map
     */
    private void buildChildren(MindMapNodeTree parentTree, Map<Long, List<MindMapNode>> nodesByParentId) {
        // 获取当前节点的所有子节点
        List<MindMapNode> children = nodesByParentId.get(parentTree.getId());

        if (children == null || children.isEmpty()) {
            return;
        }

        // 为每个子节点创建子树，并递归构建
        for (MindMapNode child : children) {
            MindMapNodeTree childTree = MindMapNodeTree.fromMindMapNode(child);
            parentTree.getChildren().add(childTree);

            // 递归构建子节点的子节点
            buildChildren(childTree, nodesByParentId);
        }
    }
}