package com.readify.server.infrastructure.persistence.repository;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.readify.server.domain.conversation.entity.ConversationHistory;
import com.readify.server.domain.conversation.entity.AssistantThinking;
import com.readify.server.domain.conversation.repository.ConversationRepository;
import com.readify.server.infrastructure.persistence.converter.ConversationConverter;
import com.readify.server.infrastructure.persistence.entity.ConversationHistoryEntity;
import com.readify.server.infrastructure.persistence.entity.AssistantThinkingEntity;
import com.readify.server.infrastructure.persistence.mapper.ConversationHistoryMapper;
import com.readify.server.infrastructure.persistence.mapper.AssistantThinkingMapper;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Repository;

import java.util.List;
import java.util.Optional;
import java.util.stream.Collectors;

@Repository
@RequiredArgsConstructor
public class ConversationRepositoryImpl implements ConversationRepository {

    private final ConversationHistoryMapper conversationHistoryMapper;
    private final AssistantThinkingMapper assistantThinkingMapper;
    private final ConversationConverter conversationConverter;

    @Override
    public List<ConversationHistory> findByProjectId(Long projectId) {
        LambdaQueryWrapper<ConversationHistoryEntity> wrapper = new LambdaQueryWrapper<>();
        wrapper.eq(ConversationHistoryEntity::getProjectId, projectId)
               .orderByAsc(ConversationHistoryEntity::getSequence);
        
        return conversationHistoryMapper.selectList(wrapper)
                .stream()
                .map(conversationConverter::toDomain)
                .collect(Collectors.toList());
    }

    @Override
    public Optional<AssistantThinking> findThinkingByUserMessageId(Long userMessageId) {
        LambdaQueryWrapper<AssistantThinkingEntity> wrapper = new LambdaQueryWrapper<>();
        wrapper.eq(AssistantThinkingEntity::getUserMessageId, userMessageId);
        
        AssistantThinkingEntity entity = assistantThinkingMapper.selectOne(wrapper);
        return Optional.ofNullable(entity).map(conversationConverter::toDomain);
    }

    @Override
    public List<AssistantThinking> findThinkingsByProjectId(Long projectId) {
        LambdaQueryWrapper<AssistantThinkingEntity> wrapper = new LambdaQueryWrapper<>();
        wrapper.eq(AssistantThinkingEntity::getProjectId, projectId);
        
        return assistantThinkingMapper.selectList(wrapper)
                .stream()
                .map(conversationConverter::toDomain)
                .collect(Collectors.toList());
    }
} 