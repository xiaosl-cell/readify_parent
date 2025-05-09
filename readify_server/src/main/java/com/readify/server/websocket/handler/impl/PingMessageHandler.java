package com.readify.server.websocket.handler.impl;

import com.readify.server.websocket.WebSocketSessionManager;
import com.readify.server.websocket.handler.WebSocketMessageHandler;
import com.readify.server.websocket.message.WebSocketMessage;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Component;
import org.springframework.web.socket.WebSocketSession;

/**
 * Ping消息处理器
 */
@Slf4j
@Component
@RequiredArgsConstructor
public class PingMessageHandler implements WebSocketMessageHandler<Void> {
    
    private final WebSocketSessionManager sessionManager;
    
    @Override
    public String supportType() {
        return "ping";
    }
    
    @Override
    public Class<Void> getDataType() {
        return Void.class;
    }
    
    @Override
    public void processMessage(WebSocketSession session, WebSocketMessage<Void> message) {
        log.debug("Processing ping message from session: {}", session.getId());
        WebSocketMessage<String> pongMessage = WebSocketMessage.create("pong", "Server is alive");
        sessionManager.sendMessage(session.getId(), pongMessage);
    }
} 