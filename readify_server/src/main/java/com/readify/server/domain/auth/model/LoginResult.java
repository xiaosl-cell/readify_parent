package com.readify.server.domain.auth.model;

import lombok.AllArgsConstructor;
import lombok.Data;

@Data
@AllArgsConstructor
public class LoginResult {
    private AuthUser user;
    private String token;
} 