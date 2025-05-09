package com.readify.server.websocket.handler;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.readify.server.websocket.WebSocketSessionManager;
import com.readify.server.websocket.message.WebSocketMessage;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Component;
import org.springframework.web.socket.WebSocketSession;

import java.util.HashMap;
import java.util.List;
import java.util.Map;

/**
 * WebSocket消息处理器管理类
 * 负责注册和查找消息处理器
 */
@Slf4j
@Component
@SuppressWarnings("all")
public class WebSocketMessageHandlerManager {
    
    private final Map<String, WebSocketMessageHandler> handlers = new HashMap<>();
    private final WebSocketSessionManager sessionManager;
    private final ObjectMapper objectMapper;
    
    @Autowired
    public WebSocketMessageHandlerManager(List<WebSocketMessageHandler> handlerList, 
                                         WebSocketSessionManager sessionManager,
                                         ObjectMapper objectMapper) {
        this.sessionManager = sessionManager;
        this.objectMapper = objectMapper;
        
        // 注册所有消息处理器
        for (WebSocketMessageHandler handler : handlerList) {
            handlers.put(handler.supportType(), handler);
            log.info("Registered WebSocket message handler for type: {}", handler.supportType());
        }
    }
    
    /**
     * 处理消息
     * @param session WebSocket会话
     * @param messageType 消息类型
     * @param rawMessage 原始消息文本
     * @return 是否成功处理
     */
    public boolean handleMessage(WebSocketSession session, String messageType, String rawMessage) {
        WebSocketMessageHandler handler = handlers.get(messageType);
        
        if (handler == null) {
            log.warn("No handler found for message type: {}", messageType);
            WebSocketMessage<String> errorMessage = WebSocketMessage.create("error", "Unknown message type: " + messageType);
            sessionManager.sendMessage(session.getId(), errorMessage);
            return false;
        }
        
        try {
            // 让每个处理器自己处理原始消息
            handler.handle(session, rawMessage, objectMapper);
            return true;
        } catch (Exception e) {
            log.error("Error handling message of type {}: {}", messageType, e.getMessage(), e);
            WebSocketMessage<String> errorMessage = WebSocketMessage.create("error", "Failed to process message: " + e.getMessage());
            sessionManager.sendMessage(session.getId(), errorMessage);
            return false;
        }
    }
    
    /**
     * 处理消息（兼容旧方法，已弃用）
     * @deprecated 使用 {@link #handleMessage(WebSocketSession, String, String)} 代替
     */
    @Deprecated
    public boolean handleMessage(WebSocketSession session, WebSocketMessage<?> message) {
        return handleMessage(session, message.getType(), objectMapper.valueToTree(message).toString());
    }
} 