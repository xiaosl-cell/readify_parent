package com.readify.server.infrastructure.common.exception;

public class NotFoundException extends BusinessException {
    public NotFoundException(String message) {
        super("404", message);
    }

    public NotFoundException() {
        this("资源未找到");
    }
} 