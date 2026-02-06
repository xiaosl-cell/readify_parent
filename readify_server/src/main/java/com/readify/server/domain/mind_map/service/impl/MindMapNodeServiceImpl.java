package com.readify.server.domain.mind_map.service.impl;

import com.readify.server.domain.mind_map.model.MindMapNode;
import com.readify.server.domain.mind_map.model.MindMapNodeTree;
import com.readify.server.domain.mind_map.repository.MindMapNodeRepository;
import com.readify.server.domain.mind_map.service.MindMapNodeService;
import com.readify.server.domain.mind_map.service.MindMapService;
import com.readify.server.infrastructure.common.exception.NotFoundException;
import lombok.RequiredArgsConstructor;
import lombok.Setter;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.context.annotation.Lazy;
import org.springframework.stereotype.Service;

import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.stream.Collectors;

@Service
@RequiredArgsConstructor
public class MindMapNodeServiceImpl implements MindMapNodeService {
    private final MindMapNodeRepository mindMapNodeRepository;

    @Setter(onMethod_ = {@Autowired, @Lazy})
    private MindMapService mindMapService;

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
        MindMapNode rootNode = mindMapNodeRepository.findRootNodeByFileId(fileId)
                .orElseThrow(() -> new NotFoundException("思维导图根节点不存在"));

        List<MindMapNode> allNodes = mindMapNodeRepository.findByFileId(fileId);
        return buildMindMapTree(rootNode, allNodes);
    }

    @Override
    public MindMapNodeTree getFullMindMap(Long mindMapId, Long userId) {
        mindMapService.getMindMapById(mindMapId, userId);

        MindMapNode rootNode = mindMapNodeRepository.findRootNodeByMindMapId(mindMapId)
                .orElseThrow(() -> new NotFoundException("思维导图根节点不存在"));
        List<MindMapNode> allNodes = mindMapNodeRepository.findByMindMapId(mindMapId);
        return buildMindMapTree(rootNode, allNodes);
    }

    @Override
    public MindMapNodeTree getSubTreeByNodeId(Long nodeId, Long userId) {
        MindMapNode node = mindMapNodeRepository.findById(nodeId)
                .orElseThrow(() -> new NotFoundException("思维导图节点不存在"));

        if (node.getMindMapId() == null) {
            throw new NotFoundException("节点未关联思维导图");
        }
        mindMapService.getMindMapById(node.getMindMapId(), userId);

        List<MindMapNode> allNodes = mindMapNodeRepository.findByMindMapId(node.getMindMapId());
        return buildMindMapTree(node, allNodes);
    }

    private MindMapNodeTree buildMindMapTree(MindMapNode rootNode, List<MindMapNode> allNodes) {
        MindMapNodeTree rootTree = MindMapNodeTree.fromMindMapNode(rootNode);
        Map<Long, List<MindMapNode>> nodesByParentId = allNodes.stream()
                .filter(node -> node.getParentId() != null)
                .collect(Collectors.groupingBy(MindMapNode::getParentId));
        buildChildren(rootTree, nodesByParentId);
        return rootTree;
    }

    private void buildChildren(MindMapNodeTree parentTree, Map<Long, List<MindMapNode>> nodesByParentId) {
        List<MindMapNode> children = nodesByParentId.get(parentTree.getId());
        if (children == null || children.isEmpty()) {
            return;
        }

        for (MindMapNode child : children) {
            MindMapNodeTree childTree = MindMapNodeTree.fromMindMapNode(child);
            parentTree.getChildren().add(childTree);
            buildChildren(childTree, nodesByParentId);
        }
    }
}

