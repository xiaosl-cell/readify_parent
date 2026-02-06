package com.readify.server.interfaces.admin.req;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.Data;

@Data
@Schema(description = "更新角色请求")
public class RoleUpdateReq {
    @Schema(description = "角色编码")
    private String code;

    @Schema(description = "角色名称")
    private String name;

    @Schema(description = "角色描述")
    private String description;

    @Schema(description = "是否启用")
    private Boolean enabled;
}
