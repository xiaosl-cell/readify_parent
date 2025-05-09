package com.readify.server.websocket.handler;

import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.JavaType;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.type.TypeFactory;
import com.readify.server.websocket.message.WebSocketMessage;
import org.springframework.web.socket.WebSocketSession;

import java.io.IOException;

/**
 * WebSocket消息处理器接口
 * 每种消息类型对应一个具体的处理器实现
 */
public interface WebSocketMessageHandler<T> {
    
    /**
     * 获取此处理器支持的消息类型
     * @return 消息类型字符串
     */
    String supportType();
    
    /**
     * 处理WebSocket消息
     * @param session WebSocket会话
     * @param message 接收到的消息
     * @deprecated 使用 {@link #handle(WebSocketSession, String, ObjectMapper)} 代替
     */
    @Deprecated
    default void handle(WebSocketSession session, WebSocketMessage<T> message) {
        throw new UnsupportedOperationException("This method is deprecated. Use handle(WebSocketSession, String, ObjectMapper) instead.");
    }
    
    /**
     * 处理WebSocket原始消息
     * @param session WebSocket会话
     * @param rawMessage 原始消息文本
     * @param objectMapper Jackson对象映射器
     * @throws IOException 如果解析消息时发生错误
     */
    default void handle(WebSocketSession session, String rawMessage, ObjectMapper objectMapper) throws IOException {
        // 获取泛型类型
        JavaType type = TypeFactory.defaultInstance().constructParametricType(WebSocketMessage.class, getDataType());
        
        // 使用正确的类型信息反序列化消息
        WebSocketMessage<T> message = objectMapper.readValue(rawMessage, type);
        
        // 调用具体处理逻辑
        processMessage(session, message);
    }
    
    /**
     * 获取数据字段的类型
     * @return 数据字段的类
     */
    Class<T> getDataType();
    
    /**
     * 处理消息的具体逻辑
     * @param session WebSocket会话
     * @param message 类型安全的消息对象
     */
    void processMessage(WebSocketSession session, WebSocketMessage<T> message);
} 