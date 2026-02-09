package com.readify.server.websocket.handler.impl;

import com.readify.server.domain.file.model.File;
import com.readify.server.domain.project.service.ProjectFileService;
import com.readify.server.infrastructure.security.SecurityUtils;
import com.readify.server.infrastructure.security.UserInfo;
import com.readify.server.websocket.WebSocketSessionManager;
import com.readify.server.websocket.dto.QueryProjectReq;
import com.readify.server.websocket.handler.WebSocketMessageHandler;
import com.readify.server.websocket.message.WebSocketMessage;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Component;
import org.springframework.web.socket.WebSocketSession;

import java.util.List;
import java.util.Optional;

/**
 * 查询项目文件消息处理器
 */
@Slf4j
@Component
@RequiredArgsConstructor
public class QueryProjectFilesHandler implements WebSocketMessageHandler<QueryProjectReq> {

    private final WebSocketSessionManager sessionManager;
    private final ProjectFileService projectFileService;

    @Override
    public String supportType() {
        return "queryProjectFiles";
    }

    @Override
    public Class<QueryProjectReq> getDataType() {
        return QueryProjectReq.class;
    }

    @Override
    public void processMessage(WebSocketSession session, WebSocketMessage<QueryProjectReq> message) {
        Long userId = getUserIdFromSession(session);
        log.debug("Processing queryProjectFiles message from user {}, session: {}", userId, session.getId());

        QueryProjectReq queryProjectReq = message.getData();
        Long projectId = Optional.ofNullable(queryProjectReq).map(QueryProjectReq::getProjectId).orElseThrow();

        // 调用服务查询项目文件
        List<File> projectFiles = projectFileService.getProjectFiles(projectId, userId);

        // 返回结果
        WebSocketMessage<List<File>> responseMessage = WebSocketMessage.create("projectFiles", projectFiles);
        sessionManager.sendMessage(session.getId(), responseMessage);
    }

    private Long getUserIdFromSession(WebSocketSession session) {
        Object userIdObj = session.getAttributes().get("userId");
        if (userIdObj instanceof Number number) {
            return number.longValue();
        }
        if (userIdObj instanceof String userIdStr) {
            try {
                return Long.parseLong(userIdStr);
            } catch (NumberFormatException ignored) {
            }
        }

        UserInfo userInfo = (UserInfo) session.getAttributes().get("userInfo");
        if (userInfo != null && userInfo.getId() != null) {
            return userInfo.getId();
        }

        try {
            return SecurityUtils.getCurrentUserId();
        } catch (Exception ignored) {
            return null;
        }
    }
}
