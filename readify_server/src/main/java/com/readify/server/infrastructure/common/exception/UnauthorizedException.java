package com.readify.server.infrastructure.common.exception;

public class UnauthorizedException extends BusinessException {
    public UnauthorizedException(String message) {
        super("401", message);
    }

    public UnauthorizedException() {
        this("未授权的访问");
    }
} 