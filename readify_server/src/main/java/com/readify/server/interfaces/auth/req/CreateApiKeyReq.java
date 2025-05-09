package com.readify.server.interfaces.auth.req;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.Data;

@Data
@Schema(description = "创建API Key请求")
public class CreateApiKeyReq {
    @Schema(description = "API Key名称")
    private String name;

    @Schema(description = "API Key描述")
    private String description;
} 