package com.readify.server.interfaces.mind_map.vo;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.Data;

@Data
@Schema(description = "思维导图视图对象")
public class MindMapVO {
    @Schema(description = "思维导图ID", accessMode = Schema.AccessMode.READ_ONLY)
    private Long id;

    @Schema(description = "工程ID", example = "1")
    private Long projectId;
    
    @Schema(description = "文件ID", example = "1")
    private Long fileId;

    @Schema(description = "思维导图标题", example = "书名")
    private String title;

    @Schema(description = "笔记类型", example = "mind_map")
    private String type;

    @Schema(description = "思维导图描述", example = "这是一个项目架构分析图")
    private String description;
}