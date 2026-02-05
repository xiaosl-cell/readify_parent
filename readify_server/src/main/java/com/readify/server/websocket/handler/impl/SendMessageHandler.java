package com.readify.server.websocket.handler.impl;

import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.readify.server.websocket.WebSocketSessionManager;
import com.readify.server.websocket.dto.SendMessageReq;
import com.readify.server.websocket.handler.WebSocketMessageHandler;
import com.readify.server.websocket.message.WebSocketMessage;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.core.ParameterizedTypeReference;
import org.springframework.http.codec.ServerSentEvent;
import org.springframework.stereotype.Component;
import org.springframework.web.reactive.function.client.WebClient;
import org.springframework.web.socket.WebSocketSession;
import reactor.core.publisher.Flux;

import java.nio.charset.StandardCharsets;
import java.util.HashMap;
import java.util.Map;
import java.util.Optional;

/**
 * 发送消息处理器
 * 接收消息请求并转发到SSE接口
 */
@Slf4j
@Component
@RequiredArgsConstructor
public class SendMessageHandler implements WebSocketMessageHandler<SendMessageReq> {
    
    private final WebSocketSessionManager sessionManager;
    private final WebClient webClient;
    
    @Override
    public String supportType() {
        return "sendMessage";
    }
    
    @Override
    public Class<SendMessageReq> getDataType() {
        return SendMessageReq.class;
    }
    
    @Override
    public void processMessage(WebSocketSession session, WebSocketMessage<SendMessageReq> message) {
        Long userId = getUserIdFromSession(session);
        log.debug("Processing sendMessage from user {}, session: {}", userId, session.getId());

        SendMessageReq req = message.getData();
        String query = Optional.ofNullable(req).map(SendMessageReq::getQuery).orElseThrow();
        Long projectId = Optional.of(req).map(SendMessageReq::getProjectId).orElseThrow();

        // 请求SSE接口
        Flux<ServerSentEvent<String>> eventStream = webClient.get()
                .uri(uriBuilder -> {
                    uriBuilder
                        .path("/api/v1/agent/stream")
                        .queryParam("query", query)
                        .queryParam("project_id", projectId)
                        .queryParam("task_type", req.getTaskType());
                    
                    // 当mindMapId不为null时添加到查询参数
                    if (req.getMindMapId() != null) {
                        Map<String, Object> context = new HashMap<>();
                        context.put("mind_map_id", req.getMindMapId());
                        ObjectMapper mapper = new ObjectMapper();
                        String contextJson;
                        try {
                            contextJson = mapper.writeValueAsString(context);
                            // 对JSON字符串进行URL编码
                            contextJson = java.net.URLEncoder.encode(contextJson, StandardCharsets.UTF_8);
                            uriBuilder.queryParam("context", contextJson);
                        } catch (Exception e) {
                            log.error("Failed to process context data", e);
                            throw new RuntimeException("Failed to process context data", e);
                        }
                    }
                    
                    return uriBuilder.build();
                })
                .retrieve()
                .bodyToFlux(new ParameterizedTypeReference<>() {});

        // 订阅SSE事件流并通过WebSocket发送给客户端
        eventStream
                // 检测到[DONE]时自动结束订阅（断开SSE连接）
                .takeUntil(event -> {
                    String data = (String) event.data();
                    if (data == null) {
                        return false;
                    }
                    try {
                        // 检测JSON格式的[DONE]
                        ObjectMapper mapper = new ObjectMapper();
                        JsonNode jsonNode = mapper.readTree(data);
                        return jsonNode.has("type") && "[DONE]".equals(jsonNode.get("type").asText());
                    } catch (Exception e) {
                        // 检测原始字符串格式的[DONE]
                        return "[DONE]".equals(data);
                    }
                })
                .subscribe(
                        // 收到事件时，直接转发给客户端
                        event -> {
                            String data = (String) event.data();
                            if (data != null) {
                                // 直接传递原始数据，不做转换
                                WebSocketMessage<String> responseMessage = WebSocketMessage.create("agentMessage", data);
                                sessionManager.sendMessage(session.getId(), responseMessage);
                            }
                        },
                        // 错误处理
                        error -> {
                            log.error("Error in SSE stream: {}", error.getMessage(), error);
                            WebSocketMessage<String> errorMessage = WebSocketMessage.create("error", "Failed to process agent stream: " + error.getMessage());
                            sessionManager.sendMessage(session.getId(), errorMessage);
                        },
                        // 完成时的处理
                        () -> {
                            log.debug("SSE stream completed for user {}", userId);
                            WebSocketMessage<String> completeMessage = WebSocketMessage.create("agentComplete", "Agent stream completed");
                            sessionManager.sendMessage(session.getId(), completeMessage);
                        }
                );
    }
    
    private Long getUserIdFromSession(WebSocketSession session) {
        return (Long) session.getAttributes().get("userId");
    }
} 