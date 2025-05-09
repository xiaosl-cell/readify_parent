package com.readify.server.websocket.message;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class WebSocketMessage<T> {
    /**
     * 消息类型
     */
    private String type;

    /**
     * 消息数据
     */
    private T data;

    /**
     * 创建时间
     */
    private Long timestamp;

    public static <T> WebSocketMessage<T> create(String type, T data) {
        return WebSocketMessage.<T>builder()
                .type(type)
                .data(data)
                .timestamp(System.currentTimeMillis())
                .build();
    }
} 