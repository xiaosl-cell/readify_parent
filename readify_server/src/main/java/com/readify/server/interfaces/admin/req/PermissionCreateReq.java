package com.readify.server.interfaces.admin.req;

import io.swagger.v3.oas.annotations.media.Schema;
import jakarta.validation.constraints.NotBlank;
import lombok.Data;

@Data
@Schema(description = "创建权限请求")
public class PermissionCreateReq {
    @NotBlank(message = "权限编码不能为空")
    @Schema(description = "权限编码", example = "USER:READ")
    private String code;

    @NotBlank(message = "权限名称不能为空")
    @Schema(description = "权限名称", example = "查看用户")
    private String name;

    @Schema(description = "所属模块", example = "USER")
    private String module;

    @Schema(description = "权限描述")
    private String description;

    @Schema(description = "是否启用", defaultValue = "true")
    private Boolean enabled = true;
}
