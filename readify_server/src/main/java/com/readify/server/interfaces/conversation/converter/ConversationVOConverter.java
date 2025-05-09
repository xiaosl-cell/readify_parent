package com.readify.server.interfaces.conversation.converter;

import com.readify.server.domain.conversation.entity.ConversationHistory;
import com.readify.server.interfaces.conversation.vo.ConversationVO;
import org.mapstruct.Mapper;
import org.mapstruct.Mapping;
import org.mapstruct.factory.Mappers;

@Mapper(componentModel = "spring", uses = AssistantThinkingVOConverter.class)
public interface ConversationVOConverter {

    ConversationVOConverter INSTANCE = Mappers.getMapper(ConversationVOConverter.class);

    @Mapping(target = "thinking", ignore = true)
    ConversationVO toResponseDTO(ConversationHistory conversation);
} 