package com.readify.server.infrastructure.common.exception;

public class ForbiddenException extends BusinessException {
    public ForbiddenException(String message) {
        super("403", message);
    }

    public ForbiddenException() {
        this("禁止访问");
    }
} 