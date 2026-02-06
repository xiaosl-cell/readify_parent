package com.readify.server.interfaces.admin.req;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.Data;

@Data
@Schema(description = "更新权限请求")
public class PermissionUpdateReq {
    @Schema(description = "权限编码")
    private String code;

    @Schema(description = "权限名称")
    private String name;

    @Schema(description = "所属模块")
    private String module;

    @Schema(description = "权限描述")
    private String description;

    @Schema(description = "是否启用")
    private Boolean enabled;
}
