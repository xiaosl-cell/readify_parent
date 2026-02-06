package com.readify.server.interfaces.admin.vo;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
@Schema(description = "仪表盘统计数据")
public class DashboardStatsVO {
    @Schema(description = "用户总数")
    private Long userCount;

    @Schema(description = "角色总数")
    private Long roleCount;

    @Schema(description = "权限总数")
    private Long permissionCount;
}
