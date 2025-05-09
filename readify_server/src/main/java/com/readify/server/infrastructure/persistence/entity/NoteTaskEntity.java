package com.readify.server.infrastructure.persistence.entity;

import com.baomidou.mybatisplus.annotation.*;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

/**
 * 笔记任务持久化实体
 */
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
@TableName("note_task")
public class NoteTaskEntity {
    
    /**
     * 主键ID
     */
    @TableId(value = "id", type = IdType.AUTO)
    private Long id;
    
    /**
     * 用户ID
     */
    @TableField("user_id")
    private Long userId;
    
    /**
     * 关联项目ID
     */
    @TableField("project_id")
    private Long projectId;
    
    /**
     * 关联的思维导图ID
     */
    @TableField("mind_map_id")
    private Long mindMapId;
    
    /**
     * 关联的文件ID
     */
    @TableField("file_id")
    private Long fileId;
    
    /**
     * 用户提问/任务内容
     */
    @TableField("content")
    private String content;
    
    /**
     * 任务状态
     */
    @TableField("status")
    private String status;
    
    /**
     * 任务结果
     */
    @TableField("result")
    private String result;
    
    /**
     * 创建时间
     */
    @TableField("create_time")
    private Long createTime;
    
    /**
     * 更新时间
     */
    @TableField("update_time")
    private Long updateTime;
    
    /**
     * 是否删除
     */
    @TableField("deleted")
    @TableLogic
    private Boolean deleted;
} 