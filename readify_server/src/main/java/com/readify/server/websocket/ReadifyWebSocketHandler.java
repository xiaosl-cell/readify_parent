package com.readify.server.websocket;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.readify.server.infrastructure.common.exception.ForbiddenException;
import com.readify.server.infrastructure.common.exception.NotFoundException;
import com.readify.server.infrastructure.common.exception.UnauthorizedException;
import com.readify.server.infrastructure.security.SecurityUtils;
import com.readify.server.infrastructure.security.UserInfo;
import com.readify.server.websocket.handler.WebSocketMessageHandlerManager;
import com.readify.server.websocket.message.WebSocketMessage;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Component;
import org.springframework.web.socket.CloseStatus;
import org.springframework.web.socket.TextMessage;
import org.springframework.web.socket.WebSocketSession;
import org.springframework.web.socket.handler.TextWebSocketHandler;
import org.springframework.lang.NonNull;

import java.util.Map;
import java.util.NoSuchElementException;
import java.util.Optional;

@Slf4j
@Component
@RequiredArgsConstructor
public class ReadifyWebSocketHandler extends TextWebSocketHandler {
    private final ObjectMapper objectMapper;
    private final WebSocketSessionManager sessionManager;
    private final WebSocketMessageHandlerManager handlerManager;

    @Override
    public void afterConnectionEstablished(@NonNull WebSocketSession session) {
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
    protected void handleTextMessage(@NonNull WebSocketSession session, @NonNull TextMessage message) {
        try {
            // 从 session 获取完整的用户信息
            UserInfo userInfo = getUserInfoFromSession(session);

            // 设置当前用户上下文（所有 Handler 都会生效）
            SecurityUtils.setCurrentUser(userInfo);

            // 只解析消息类型，不进行完整反序列化
            Map<String, Object> messageMap = objectMapper.readValue(message.getPayload(), Map.class);
            String messageType = Optional.ofNullable((String) messageMap.get("type"))
                    .orElseThrow(() -> new IllegalArgumentException("消息类型不能为空"));

            log.debug("Received message from user {}, session {}: type={}", userInfo.getId(), session.getId(), messageType);

            // 将原始消息文本传递给处理器管理类
            handlerManager.handleMessage(session, messageType, message.getPayload());
        } catch (Exception e) {
            log.error("Error handling message", e);
            WebSocketMessage<String> errorMessage = WebSocketMessage.create("error", buildFriendlyErrorMessage(e));
            sessionManager.sendMessage(session.getId(), errorMessage);
        } finally {
            // 清除用户上下文，避免线程复用时的问题
            SecurityUtils.clearCurrentUser();
        }
    }

    @Override
    public void afterConnectionClosed(@NonNull WebSocketSession session, @NonNull CloseStatus status) {
        Long userId = getUserIdFromSession(session);
        log.info("WebSocket connection closed: {}, userId: {}, status: {}", session.getId(), userId, status);
        sessionManager.removeSession(session);
    }

    @Override
    public void handleTransportError(@NonNull WebSocketSession session, @NonNull Throwable exception) {
        Long userId = getUserIdFromSession(session);
        log.error("Transport error in session: {}, userId: {}", session.getId(), userId, exception);
        WebSocketMessage<String> errorMessage = WebSocketMessage.create("error",
                "Transport error: " + exception.getMessage());
        sessionManager.sendMessage(session.getId(), errorMessage);
    }

    private Long getUserIdFromSession(WebSocketSession session) {
        Object userId = session.getAttributes().get("userId");
        return parseUserId(userId);
    }

    private UserInfo getUserInfoFromSession(WebSocketSession session) {
        UserInfo userInfo = (UserInfo) session.getAttributes().get("userInfo");
        if (userInfo != null && userInfo.getId() != null) {
            return userInfo;
        }

        // 向后兼容：如果没有 userInfo，则从 userId 构造
        Long userId = getUserIdFromSession(session);
        if (userId == null) {
            throw new UnauthorizedException("用户未登录");
        }
        return new UserInfo(userId, null);
    }

    private Long parseUserId(Object userIdObj) {
        if (userIdObj == null) {
            return null;
        }

        if (userIdObj instanceof Number number) {
            return number.longValue();
        }

        if (userIdObj instanceof String userIdStr) {
            try {
                return Long.parseLong(userIdStr);
            } catch (NumberFormatException e) {
                return null;
            }
        }

        return null;
    }

    private String buildFriendlyErrorMessage(Exception exception) {
        Throwable rootCause = getRootCause(exception);

        if (rootCause instanceof UnauthorizedException) {
            return "登录状态已失效，请刷新页面后重新登录";
        }

        if (rootCause instanceof ForbiddenException) {
            return "无权访问该项目，请确认后重试";
        }

        if (rootCause instanceof NotFoundException) {
            return "项目不存在或已被删除";
        }

        if (rootCause instanceof IllegalArgumentException || rootCause instanceof NoSuchElementException) {
            return "请求参数不完整，请刷新页面后重试";
        }

        return "处理请求失败，请稍后重试";
    }

    private Throwable getRootCause(Throwable throwable) {
        Throwable current = throwable;
        while (current.getCause() != null && current.getCause() != current) {
            current = current.getCause();
        }
        return current;
    }
}
