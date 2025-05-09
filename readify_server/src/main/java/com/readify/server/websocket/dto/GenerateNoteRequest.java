package com.readify.server.websocket.dto;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

/**
 * 生成笔记请求DTO
 */
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class GenerateNoteRequest {
    
    /**
     * 项目ID
     */
    private Long projectId;
    
    /**
     * 思维导图ID
     */
    private Long mindMapId;
    
    /**
     * 用户指令内容
     */
    private String query;
} 