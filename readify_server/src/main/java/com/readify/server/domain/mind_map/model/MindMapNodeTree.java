package com.readify.server.domain.mind_map.model;

import lombok.Data;

import java.util.ArrayList;
import java.util.List;

@Data
public class MindMapNodeTree {
    private Long id;
    private Long projectId;
    private Long fileId;
    private Long mindMapId;
    private Long parentId;
    private String content;
    private Integer sequence;
    private Integer level;
    private Long createdTime;
    private Long updatedTime;
    private List<MindMapNodeTree> children = new ArrayList<>();
    
    public static MindMapNodeTree fromMindMapNode(MindMapNode node) {
        MindMapNodeTree tree = new MindMapNodeTree();
        tree.setId(node.getId());
        tree.setProjectId(node.getProjectId());
        tree.setFileId(node.getFileId());
        tree.setMindMapId(node.getMindMapId());
        tree.setParentId(node.getParentId());
        tree.setContent(node.getContent());
        tree.setSequence(node.getSequence());
        tree.setLevel(node.getLevel());
        tree.setCreatedTime(node.getCreatedTime());
        tree.setUpdatedTime(node.getUpdatedTime());
        return tree;
    }
} 