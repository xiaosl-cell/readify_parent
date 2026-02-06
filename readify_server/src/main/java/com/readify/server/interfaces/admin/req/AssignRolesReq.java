package com.readify.server.interfaces.admin.req;

import io.swagger.v3.oas.annotations.media.Schema;
import jakarta.validation.constraints.NotNull;
import lombok.Data;

import java.util.List;

@Data
@Schema(description = "分配角色请求")
public class AssignRolesReq {
    @NotNull(message = "角色ID列表不能为空")
    @Schema(description = "角色ID列表")
    private List<Long> roleIds;
}
