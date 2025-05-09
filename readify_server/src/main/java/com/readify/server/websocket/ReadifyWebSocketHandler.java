package com.readify.server.websocket;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.readify.server.websocket.handler.WebSocketMessageHandlerManager;
import com.readify.server.websocket.message.WebSocketMessage;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Component;
import org.springframework.web.socket.CloseStatus;
import org.springframework.web.socket.TextMessage;
import org.springframework.web.socket.WebSocketSession;
import org.springframework.web.socket.handler.TextWebSocketHandler;

import java.util.Map;

@Slf4j
@Component
@RequiredArgsConstructor
public class ReadifyWebSocketHandler extends TextWebSocketHandler {
    private final ObjectMapper objectMapper;
    private final WebSocketSessionManager sessionManager;
    private final WebSocketMessageHandlerManager handlerManager;

    @Override
    public void afterConnectionEstablished(WebSocketSession session) {
        Long userId = getUserIdFromSession(session);
        log.info("New WebSocket connection established: {}, userId: {}", session.getId(), userId);
        sessionManager.addSession(session);
        
        // 发送连接成功消息
        WebSocketMessage<String> message = WebSocketMessage.create("connected", 
            String.format("Connection established successfully for user %d", userId));
        sessionManager.sendMessage(session.getId(), message);
    }

    @Override
    @SuppressWarnings("all")
    protected void handleTextMessage(WebSocketSession session, TextMessage message) {
        try {
            // 只解析消息类型，不进行完整反序列化
            Map<String, Object> messageMap = objectMapper.readValue(message.getPayload(), Map.class);
            String messageType = (String) messageMap.get("type");
            
            Long userId = getUserIdFromSession(session);
            log.debug("Received message from user {}, session {}: type={}", userId, session.getId(), messageType);

            // 将原始消息文本传递给处理器管理类
            handlerManager.handleMessage(session, messageType, message.getPayload());
        } catch (Exception e) {
            log.error("Error handling message", e);
            WebSocketMessage<String> errorMessage = WebSocketMessage.create("error", "Failed to process message: " + e.getMessage());
            sessionManager.sendMessage(session.getId(), errorMessage);
        }
    }

    @Override
    public void afterConnectionClosed(WebSocketSession session, CloseStatus status) {
        Long userId = getUserIdFromSession(session);
        log.info("WebSocket connection closed: {}, userId: {}, status: {}", session.getId(), userId, status);
        sessionManager.removeSession(session);
    }

    @Override
    public void handleTransportError(WebSocketSession session, Throwable exception) {
        Long userId = getUserIdFromSession(session);
        log.error("Transport error in session: {}, userId: {}", session.getId(), userId, exception);
        WebSocketMessage<String> errorMessage = WebSocketMessage.create("error", "Transport error: " + exception.getMessage());
        sessionManager.sendMessage(session.getId(), errorMessage);
    }

    private Long getUserIdFromSession(WebSocketSession session) {
        return (Long) session.getAttributes().get("userId");
    }
} 