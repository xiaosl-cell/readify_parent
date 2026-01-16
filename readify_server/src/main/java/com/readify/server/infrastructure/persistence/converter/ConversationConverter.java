package com.readify.server.infrastructure.persistence.converter;

import com.readify.server.domain.conversation.entity.AssistantThinking;
import com.readify.server.domain.conversation.entity.ConversationHistory;
import com.readify.server.infrastructure.persistence.entity.AssistantThinkingEntity;
import com.readify.server.infrastructure.persistence.entity.ConversationHistoryEntity;
import org.mapstruct.Mapper;
import org.mapstruct.factory.Mappers;

@Mapper(componentModel = "spring")
public interface ConversationConverter {

    ConversationConverter INSTANCE = Mappers.getMapper(ConversationConverter.class);

    ConversationHistory toDomain(ConversationHistoryEntity entity);

    ConversationHistoryEntity toEntity(ConversationHistory domain);

    AssistantThinking toDomain(AssistantThinkingEntity entity);

    AssistantThinkingEntity toEntity(AssistantThinking domain);
}