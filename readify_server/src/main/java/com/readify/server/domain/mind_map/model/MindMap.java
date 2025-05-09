package com.readify.server.domain.mind_map.model;

import lombok.Data;

@Data
public class MindMap {
    private Long id;
    private Long projectId;
    private Long fileId;
    private String title;
    private String type;
    private String description;
    private Long userId;
    private Long createdAt;
    private Long updatedAt;
    private Boolean isDeleted;
} 