package com.readify.server.domain.conversation.entity;

import lombok.Data;
import lombok.Builder;
import lombok.NoArgsConstructor;
import lombok.AllArgsConstructor;

import java.time.LocalDateTime;

@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class AssistantThinking {
    private Long id;
    private Long projectId;
    private Long userMessageId;
    private String content;
    private LocalDateTime createdAt;
    private LocalDateTime updatedAt;
} 