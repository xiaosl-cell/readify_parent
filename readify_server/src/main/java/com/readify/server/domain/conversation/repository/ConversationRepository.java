package com.readify.server.domain.conversation.repository;

import com.readify.server.domain.conversation.entity.ConversationHistory;
import com.readify.server.domain.conversation.entity.AssistantThinking;

import java.util.List;
import java.util.Optional;

public interface ConversationRepository {
    /**
     * 根据项目ID获取对话历史列表
     */
    List<ConversationHistory> findByProjectId(Long projectId);
    
    /**
     * 根据用户消息ID获取思考过程
     */
    Optional<AssistantThinking> findThinkingByUserMessageId(Long userMessageId);
    
    /**
     * 根据项目ID获取所有用户消息相关的思考过程
     */
    List<AssistantThinking> findThinkingsByProjectId(Long projectId);
} 