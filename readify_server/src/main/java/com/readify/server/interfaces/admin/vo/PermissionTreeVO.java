package com.readify.server.interfaces.admin.vo;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.util.List;
import java.util.Map;

@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
@Schema(description = "权限树视图对象")
public class PermissionTreeVO {
    @Schema(description = "按模块分组的权限树")
    private Map<String, List<PermissionVO>> tree;
}
