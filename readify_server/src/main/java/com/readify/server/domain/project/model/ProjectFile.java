package com.readify.server.domain.project.model;

import lombok.Builder;
import lombok.Data;

@Data
@Builder
public class ProjectFile {
    private Long id;
    private Long projectId;
    private Long userId;
    private Long fileId;
    private Long createTime;
    private Long updateTime;
    private Boolean deleted;
} 