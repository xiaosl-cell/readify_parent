package com.readify.server.websocket.handler.impl;

import com.readify.server.websocket.WebSocketSessionManager;
import com.readify.server.websocket.handler.WebSocketMessageHandler;
import com.readify.server.websocket.message.WebSocketMessage;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Component;
import org.springframework.web.socket.WebSocketSession;

/**
 * 广播消息处理器
 */
@Slf4j
@Component
@RequiredArgsConstructor
public class BroadcastMessageHandler implements WebSocketMessageHandler<String> {
    
    private final WebSocketSessionManager sessionManager;
    
    @Override
    public String supportType() {
        return "broadcast";
    }
    
    @Override
    public Class<String> getDataType() {
        return String.class;
    }
    
    @Override
    public void processMessage(WebSocketSession session, WebSocketMessage<String> message) {
        Long userId = getUserIdFromSession(session);
        log.debug("Processing broadcast message from user {}, session: {}", userId, session.getId());
        
        // 在广播消息中添加发送者信息
        WebSocketMessage<String> broadcastMessage = WebSocketMessage.create(
            "broadcast", 
            String.format("Message from user %d: %s", userId, message.getData())
        );
        sessionManager.broadcastMessage(broadcastMessage);
    }
    
    private Long getUserIdFromSession(WebSocketSession session) {
        return (Long) session.getAttributes().get("userId");
    }
} 