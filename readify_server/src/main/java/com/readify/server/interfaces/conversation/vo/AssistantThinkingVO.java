package com.readify.server.interfaces.conversation.vo;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.Data;
import lombok.Builder;
import lombok.NoArgsConstructor;
import lombok.AllArgsConstructor;

import java.time.LocalDateTime;

@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
@Schema(description = "AI思考过程视图对象")
public class AssistantThinkingVO {
    @Schema(description = "思考过程ID", example = "1")
    private Long id;
    
    @Schema(description = "关联的用户消息ID", example = "10")
    private Long userMessageId;
    
    @Schema(description = "思考过程内容")
    private String content;
    
    @Schema(description = "创建时间", example = "2025-03-07T12:00:00")
    private LocalDateTime createdAt;
} 