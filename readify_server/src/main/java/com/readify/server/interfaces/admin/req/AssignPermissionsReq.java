package com.readify.server.interfaces.admin.req;

import io.swagger.v3.oas.annotations.media.Schema;
import jakarta.validation.constraints.NotNull;
import lombok.Data;

import java.util.List;

@Data
@Schema(description = "分配权限请求")
public class AssignPermissionsReq {
    @NotNull(message = "权限ID列表不能为空")
    @Schema(description = "权限ID列表")
    private List<Long> permissionIds;
}
