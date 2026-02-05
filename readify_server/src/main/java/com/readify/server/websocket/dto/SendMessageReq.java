package com.readify.server.websocket.dto;

import lombok.Data;

@Data
public class SendMessageReq {
    /**
     * 项目id
     */
    private Long projectId;
    /**
     * 任务模式
     */
    private String taskType;
    /**
     * 思维导图id
     */
    private Long mindMapId = null;
    /**
     * 用户输入
     */
    private String query;
}