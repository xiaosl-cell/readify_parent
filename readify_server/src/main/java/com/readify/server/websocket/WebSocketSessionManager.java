package com.readify.server.websocket;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.readify.server.websocket.message.WebSocketMessage;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Component;
import org.springframework.web.socket.TextMessage;
import org.springframework.web.socket.WebSocketSession;

import java.io.IOException;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;

@Slf4j
@Component
@RequiredArgsConstructor
public class WebSocketSessionManager {
    private final ObjectMapper objectMapper;
    private final Map<String, WebSocketSession> sessions = new ConcurrentHashMap<>();
    private final Map<Long, String> userSessionMap = new ConcurrentHashMap<>();

    /**
     * 添加会话
     */
    public void addSession(WebSocketSession session) {
        sessions.put(session.getId(), session);
        Long userId = getUserIdFromSession(session);
        if (userId != null) {
            userSessionMap.put(userId, session.getId());
        }
    }

    /**
     * 移除会话
     */
    public void removeSession(WebSocketSession session) {
        sessions.remove(session.getId());
        Long userId = getUserIdFromSession(session);
        if (userId != null) {
            userSessionMap.remove(userId);
        }
    }

    /**
     * 获取会话数量
     */
    public int getSessionCount() {
        return sessions.size();
    }

    /**
     * 广播消息给所有会话
     */
    public <T> void broadcastMessage(WebSocketMessage<T> message) {
        String payload;
        try {
            payload = objectMapper.writeValueAsString(message);
        } catch (IOException e) {
            log.error("Failed to serialize message", e);
            return;
        }

        TextMessage textMessage = new TextMessage(payload);
        sessions.values().forEach(session -> {
            try {
                if (session.isOpen()) {
                    session.sendMessage(textMessage);
                }
            } catch (IOException e) {
                log.error("Failed to send message to session: " + session.getId(), e);
            }
        });
    }

    /**
     * 发送消息给指定会话
     */
    public <T> void sendMessage(String sessionId, WebSocketMessage<T> message) {
        WebSocketSession session = sessions.get(sessionId);
        if (session != null && session.isOpen()) {
            try {
                String payload = objectMapper.writeValueAsString(message);
                session.sendMessage(new TextMessage(payload));
            } catch (IOException e) {
                log.error("Failed to send message to session: " + sessionId, e);
            }
        }
    }

    /**
     * 发送消息给指定用户
     */
    public <T> void sendMessageToUser(Long userId, WebSocketMessage<T> message) {
        String sessionId = userSessionMap.get(userId);
        if (sessionId != null) {
            sendMessage(sessionId, message);
        }
    }

    /**
     * 广播消息给指定用户列表
     */
    public <T> void broadcastMessageToUsers(List<Long> userIds, WebSocketMessage<T> message) {
        userIds.forEach(userId -> sendMessageToUser(userId, message));
    }

    /**
     * 获取用户的会话ID
     */
    public String getUserSessionId(Long userId) {
        return userSessionMap.get(userId);
    }

    /**
     * 获取所有在线用户ID
     */
    public List<Long> getOnlineUserIds() {
        return new ArrayList<>(userSessionMap.keySet());
    }

    /**
     * 检查用户是否在线
     */
    public boolean isUserOnline(Long userId) {
        String sessionId = userSessionMap.get(userId);
        if (sessionId != null) {
            WebSocketSession session = sessions.get(sessionId);
            return session != null && session.isOpen();
        }
        return false;
    }

    private Long getUserIdFromSession(WebSocketSession session) {
        return (Long) session.getAttributes().get("userId");
    }
} 