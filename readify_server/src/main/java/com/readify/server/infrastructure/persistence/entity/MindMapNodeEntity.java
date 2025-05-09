package com.readify.server.infrastructure.persistence.entity;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableLogic;
import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Data;

@Data
@TableName("mind_map_node")
public class MindMapNodeEntity {
    /**
     * 节点唯一标识
     */
    @TableId(type = IdType.AUTO)
    private Long id;

    /**
     * 项目ID
     */
    private Long projectId;

    /**
     * 所属文件ID
     */
    private Long fileId;

    /**
     * 所属思维导图ID
     */
    private Long mindMapId;

    /**
     * 父节点ID，根节点为NULL
     */
    private Long parentId;

    /**
     * 节点内容
     */
    private String content;

    /**
     * 同级节点间的排序顺序
     */
    private Integer sequence;

    /**
     * 节点层级，根节点为0
     */
    private Integer level;

    /**
     * 创建时间
     */
    private Long createdTime;

    /**
     * 更新时间
     */
    private Long updatedTime;

    /**
     * 是否删除，0-未删除，1-已删除
     */
    @TableLogic
    private Boolean deleted;
} 