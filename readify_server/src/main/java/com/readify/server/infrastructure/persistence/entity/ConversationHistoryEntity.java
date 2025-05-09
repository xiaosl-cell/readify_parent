package com.readify.server.infrastructure.persistence.entity;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Data;

import java.time.LocalDateTime;

@Data
@TableName("conversation_history")
public class ConversationHistoryEntity {
    @TableId(type = IdType.AUTO)
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