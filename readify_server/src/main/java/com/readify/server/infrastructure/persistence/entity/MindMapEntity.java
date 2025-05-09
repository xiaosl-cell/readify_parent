package com.readify.server.infrastructure.persistence.entity;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableLogic;
import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Data;

@Data
@TableName("mind_map")
public class MindMapEntity {
    /**
     * 思维导图ID
     */
    @TableId(type = IdType.AUTO)
    private Long id;

    /**
     * 工程ID
     */
    private Long projectId;

    /**
     * 文件id
     */
    private Long fileId;

    /**
     * 思维导图标题
     */
    private String title;

    /**
     * 笔记类型
     */
    private String type;

    /**
     * 思维导图描述
     */
    private String description;

    /**
     * 用户ID
     */
    private Long userId;

    /**
     * 创建时间
     */
    private Long createdAt;

    /**
     * 更新时间
     */
    private Long updatedAt;

    /**
     * 是否删除
     */
    @TableLogic
    private Boolean isDeleted;
} 