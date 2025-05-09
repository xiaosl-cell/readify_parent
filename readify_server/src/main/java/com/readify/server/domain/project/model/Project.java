package com.readify.server.domain.project.model;

import lombok.Data;

@Data
public class Project {
    private Long id;
    private Long userId;
    private String name;
    private String description;
    private Long createTime;
    private Long updateTime;
} 