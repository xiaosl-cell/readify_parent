package com.readify.server.interfaces.project.vo;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.Data;

@Data
@Schema(description = "工程视图对象")
public class ProjectVO {
    @Schema(description = "工程ID", accessMode = Schema.AccessMode.READ_ONLY)
    private Long id;

    @Schema(description = "用户ID", accessMode = Schema.AccessMode.READ_ONLY)
    private Long userId;

    @Schema(description = "工程名称", example = "示例工程")
    private String name;

    @Schema(description = "工程描述", example = "这是一个示例工程")
    private String description;

    @Schema(description = "创建时间", accessMode = Schema.AccessMode.READ_ONLY)
    private Long createTime;

    @Schema(description = "更新时间", accessMode = Schema.AccessMode.READ_ONLY)
    private Long updateTime;
} 