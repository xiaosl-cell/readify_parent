package com.readify.server.domain.conversation.service;

import com.readify.server.interfaces.conversation.vo.ConversationVO;

import java.util.List;

public interface ConversationService {
    /**
     * 根据项目ID获取对话历史列表，关联用户消息的思考过程
     *
     * @param projectId 项目ID
     * @return 对话历史视图对象列表
     */
    List<ConversationVO> getConversationsByProjectId(Long projectId);
} 