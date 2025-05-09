package com.readify.server.interfaces.file.req;

import lombok.Data;

@Data
public class VectorizedCallbackReq {
    private Long fileId;
    private Boolean success;
    private String message;
    private Long timestamp;
}
