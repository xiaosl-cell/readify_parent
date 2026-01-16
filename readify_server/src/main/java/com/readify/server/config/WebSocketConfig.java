package com.readify.server.config;

import com.readify.server.websocket.ReadifyWebSocketHandler;
import com.readify.server.websocket.WebSocketAuthInterceptor;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.context.annotation.Configuration;
import org.springframework.web.socket.config.annotation.EnableWebSocket;
import org.springframework.web.socket.config.annotation.WebSocketConfigurer;
import org.springframework.web.socket.config.annotation.WebSocketHandlerRegistry;
import org.springframework.lang.NonNull;

@Slf4j
@Configuration
@EnableWebSocket
@RequiredArgsConstructor
public class WebSocketConfig implements WebSocketConfigurer {

    private final ReadifyWebSocketHandler readifyWebSocketHandler;
    private final WebSocketAuthInterceptor webSocketAuthInterceptor;

    @Override
    public void registerWebSocketHandlers(@NonNull WebSocketHandlerRegistry registry) {
        // 注意：spring.mvc.servlet.path: /api/v1 会自动添加前缀
        // 所以这里只需要配置相对路径，不需要包含/api/v1
        log.info("Registering WebSocket handler at path: /ws/readify (实际访问路径: /api/v1/ws/readify)");

        registry.addHandler(readifyWebSocketHandler, "/ws/readify")
                .addInterceptors(webSocketAuthInterceptor)
                .setAllowedOrigins("*");
    }
}