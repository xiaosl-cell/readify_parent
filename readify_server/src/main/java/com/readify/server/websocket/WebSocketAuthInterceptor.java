package com.readify.server.websocket;

import com.readify.server.infrastructure.security.JwtTokenProvider;
import jakarta.servlet.http.HttpServletRequest;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.server.ServerHttpRequest;
import org.springframework.http.server.ServerHttpResponse;
import org.springframework.http.server.ServletServerHttpRequest;
import org.springframework.lang.Nullable;
import org.springframework.stereotype.Component;
import org.springframework.util.StringUtils;
import org.springframework.web.socket.WebSocketHandler;
import org.springframework.web.socket.server.HandshakeInterceptor;

import java.util.Enumeration;
import java.util.Map;

@Slf4j
@Component
@RequiredArgsConstructor
public class WebSocketAuthInterceptor implements HandshakeInterceptor {
    
    private final JwtTokenProvider jwtTokenProvider;

    @Override
    public boolean beforeHandshake(@Nullable ServerHttpRequest request, @Nullable ServerHttpResponse response,
                                   @Nullable WebSocketHandler wsHandler, @Nullable Map<String, Object> attributes) {
        if (request == null) {
            log.error("WebSocket connection rejected: Request is null");
            return false;
        }

        // 记录详细的请求信息
        log.info("===================== WebSocket连接请求 =====================");
        log.info("请求URI: {}", request.getURI());
        log.info("请求方法: {}", request.getMethod());
        log.info("请求头: {}", request.getHeaders());

        if (!(request instanceof ServletServerHttpRequest)) {
            log.error("WebSocket connection rejected: Not a ServletServerHttpRequest");
            return false;
        }

        HttpServletRequest servletRequest = ((ServletServerHttpRequest) request).getServletRequest();
        
        // 记录所有请求参数
        log.info("请求参数:");
        Enumeration<String> parameterNames = servletRequest.getParameterNames();
        while (parameterNames.hasMoreElements()) {
            String paramName = parameterNames.nextElement();
            String paramValue = servletRequest.getParameter(paramName);
            log.info("  {} = {}", paramName, paramValue);
        }
        
        String token = servletRequest.getParameter("token");
        log.info("从请求参数中获取的token: {}", token);

        if (!StringUtils.hasText(token)) {
            log.warn("WebSocket连接被拒绝: 未提供token");
            return false;
        }

        try {
            // 验证token并获取用户ID
            Long userId = jwtTokenProvider.getUserIdFromToken(token);
            log.info("Token验证结果 - userId: {}", userId);
            
            if (userId == null) {
                log.warn("WebSocket连接被拒绝: 无效的token");
                return false;
            }

            // 将用户ID存储在WebSocket会话属性中
            attributes.put("userId", userId);
            log.info("WebSocket连接已授权，用户ID: {}", userId);
            return true;
        } catch (Exception e) {
            log.error("WebSocket连接被拒绝: Token验证失败", e);
            return false;
        }
    }

    @Override
    public void afterHandshake(ServerHttpRequest request, ServerHttpResponse response,
                             WebSocketHandler wsHandler, Exception exception) {
        if (exception != null) {
            log.error("WebSocket握手过程中发生错误", exception);
        } else {
            log.info("WebSocket握手成功完成");
        }
    }
} 