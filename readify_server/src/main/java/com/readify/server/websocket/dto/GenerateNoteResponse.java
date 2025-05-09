package com.readify.server.websocket.dto;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

/**
 * 生成笔记响应DTO
 */
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class GenerateNoteResponse {
    
    /**
     * 任务ID
     */
    private Long taskId;
    
    /**
     * 项目ID
     */
    private Long projectId;
    
    /**
     * 思维导图ID
     */
    private Long mindMapId;
    
    /**
     * 响应内容，流式返回的部分内容
     */
    private String content;
    
    /**
     * 标记是否为最后一条消息
     */
    private boolean done;
} 