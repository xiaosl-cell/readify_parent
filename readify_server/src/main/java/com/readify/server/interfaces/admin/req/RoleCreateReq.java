package com.readify.server.interfaces.admin.req;

import io.swagger.v3.oas.annotations.media.Schema;
import jakarta.validation.constraints.NotBlank;
import lombok.Data;

@Data
@Schema(description = "创建角色请求")
public class RoleCreateReq {
    @NotBlank(message = "角色编码不能为空")
    @Schema(description = "角色编码", example = "ROLE_ADMIN")
    private String code;

    @NotBlank(message = "角色名称不能为空")
    @Schema(description = "角色名称", example = "管理员")
    private String name;

    @Schema(description = "角色描述")
    private String description;

    @Schema(description = "是否启用", defaultValue = "true")
    private Boolean enabled = true;
}
