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
@Schema(description = "对话记录视图对象")
public class ConversationVO {
    @Schema(description = "对话ID", example = "1")
    private Long id;
    
    @Schema(description = "项目ID", example = "100")
    private Long projectId;
    
    @Schema(description = "消息类型: SYSTEM/USER/ASSISTANT", example = "USER")
    private String messageType;
    
    @Schema(description = "消息内容")
    private String content;
    
    @Schema(description = "优先级: 数值越大优先级越高", example = "1")
    private Integer priority;
    
    @Schema(description = "是否包含在上下文中: true-包含, false-不包含", example = "true")
    private Boolean isIncludedInContext;
    
    @Schema(description = "对话序号", example = "1")
    private Integer sequence;
    
    @Schema(description = "创建时间", example = "2025-03-07T12:00:00")
    private LocalDateTime createdAt;
    
    // 仅用户消息包含思考过程
    @Schema(description = "AI思考过程，仅用户消息包含")
    private AssistantThinkingVO thinking;
} 