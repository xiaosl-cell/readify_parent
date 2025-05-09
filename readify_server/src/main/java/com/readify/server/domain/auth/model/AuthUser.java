package com.readify.server.domain.auth.model;

import lombok.Data;

@Data
public class AuthUser {
    private Long id;
    private String username;
    private String password;
    private Boolean enabled;
    private Long createTime;
    private Long updateTime;
} 