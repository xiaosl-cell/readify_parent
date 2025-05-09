package com.readify.server.interfaces.conversation.converter;

import com.readify.server.domain.conversation.entity.AssistantThinking;
import com.readify.server.interfaces.conversation.vo.AssistantThinkingVO;
import org.mapstruct.Mapper;
import org.mapstruct.factory.Mappers;

@Mapper(componentModel = "spring")
public interface AssistantThinkingVOConverter {

    AssistantThinkingVOConverter INSTANCE = Mappers.getMapper(AssistantThinkingVOConverter.class);

    AssistantThinkingVO toDTO(AssistantThinking thinking);
} 