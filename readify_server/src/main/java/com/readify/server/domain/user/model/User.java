package com.readify.server.domain.user.model;

import lombok.Data;

@Data
public class User {
    private Long id;
    private String username;
    private Boolean enabled;
    private Long createTime;
    private Long updateTime;
} 