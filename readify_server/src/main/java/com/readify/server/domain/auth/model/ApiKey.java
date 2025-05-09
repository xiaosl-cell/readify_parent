package com.readify.server.domain.auth.model;

import lombok.Data;

@Data
public class ApiKey {
    private Long id;
    private String name;
    private String apiKey;
    private String description;
    private Long userId;
    private Boolean enabled;
    private Long createTime;
    private Long updateTime;
} 