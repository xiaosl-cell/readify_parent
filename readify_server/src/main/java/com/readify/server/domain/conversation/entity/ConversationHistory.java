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
public class ConversationHistory {
    private Long id;
    private Long projectId;
    private String messageType;
    private String content;
    private Integer priority;
    private Boolean isIncludedInContext;
    private Integer sequence;
    private LocalDateTime createdAt;
    private LocalDateTime updatedAt;
} 