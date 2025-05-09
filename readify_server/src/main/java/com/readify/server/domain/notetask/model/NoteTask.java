package com.readify.server.domain.notetask.model;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

/**
 * 笔记任务领域模型
 */
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class NoteTask {
    /**
     * 主键ID
     */
    private Long id;
    
    /**
     * 用户ID
     */
    private Long userId;
    
    /**
     * 关联项目ID
     */
    private Long projectId;
    
    /**
     * 关联的思维导图ID
     */
    private Long mindMapId;
    
    /**
     * 关联的文件ID
     */
    private Long fileId;
    
    /**
     * 用户提问/任务内容
     */
    private String content;
    
    /**
     * 任务状态
     */
    private String status;
    
    /**
     * 任务结果
     */
    private String result;
    
    /**
     * 创建时间
     */
    private Long createTime;
    
    /**
     * 更新时间
     */
    private Long updateTime;
    
    /**
     * 是否删除
     */
    private Boolean deleted;
} 