package com.readify.server.domain.mind_map.model;

import lombok.Data;

@Data
public class MindMapNode {
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
    private Boolean deleted;
} 