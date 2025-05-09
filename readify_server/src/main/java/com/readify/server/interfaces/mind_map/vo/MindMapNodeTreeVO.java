package com.readify.server.interfaces.mind_map.vo;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.Data;

import java.util.ArrayList;
import java.util.List;

@Data
@Schema(description = "思维导图节点树形结构")
public class MindMapNodeTreeVO {
    @Schema(description = "节点ID")
    private Long id;

    @Schema(description = "项目ID")
    private Long projectId;

    @Schema(description = "文件ID")
    private Long fileId;

    @Schema(description = "思维导图ID")
    private Long mindMapId;

    @Schema(description = "父节点ID，根节点为null")
    private Long parentId;

    @Schema(description = "节点内容")
    private String content;

    @Schema(description = "排序序号")
    private Integer sequence;

    @Schema(description = "节点层级，根节点为0")
    private Integer level;

    @Schema(description = "创建时间")
    private Long createdTime;

    @Schema(description = "更新时间")
    private Long updatedTime;

    @Schema(description = "子节点列表")
    private List<MindMapNodeTreeVO> children = new ArrayList<>();
} 