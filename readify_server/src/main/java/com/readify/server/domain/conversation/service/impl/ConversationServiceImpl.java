package com.readify.server.domain.conversation.service.impl;

import com.readify.server.domain.conversation.entity.AssistantThinking;
import com.readify.server.domain.conversation.entity.ConversationHistory;
import com.readify.server.domain.conversation.repository.ConversationRepository;
import com.readify.server.domain.conversation.service.ConversationService;
import com.readify.server.domain.project.service.ProjectService;
import com.readify.server.interfaces.conversation.converter.AssistantThinkingVOConverter;
import com.readify.server.interfaces.conversation.converter.ConversationVOConverter;
import com.readify.server.interfaces.conversation.vo.ConversationVO;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;

import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.stream.Collectors;

@Service
@RequiredArgsConstructor
public class ConversationServiceImpl implements ConversationService {

    private final ConversationRepository conversationRepository;
    private final ProjectService projectService;
    private final ConversationVOConverter conversationVOConverter;
    private final AssistantThinkingVOConverter assistantThinkingVOConverter;

    @Override
    public List<ConversationVO> getConversationsByProjectId(Long projectId, Long userId) {
        projectService.getProjectById(projectId, userId);

        List<ConversationHistory> conversationHistoryList = conversationRepository.findByProjectId(projectId);
        List<AssistantThinking> thinkingList = conversationRepository.findThinkingsByProjectId(projectId);

        Map<Long, AssistantThinking> thinkingMap = new HashMap<>();
        thinkingList.forEach(thinking -> thinkingMap.put(thinking.getUserMessageId(), thinking));

        return conversationHistoryList.stream()
                .map(conversation -> {
                    ConversationVO vo = conversationVOConverter.toResponseDTO(conversation);
                    if ("assistant".equals(conversation.getMessageType())) {
                        Optional.ofNullable(thinkingMap.get(conversation.getId()))
                                .ifPresent(thinking -> vo.setThinking(assistantThinkingVOConverter.toDTO(thinking)));
                    }
                    return vo;
                })
                .collect(Collectors.toList());
    }
}

