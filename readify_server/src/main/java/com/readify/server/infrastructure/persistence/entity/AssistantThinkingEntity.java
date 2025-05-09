package com.readify.server.infrastructure.persistence.entity;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Data;

import java.time.LocalDateTime;

@Data
@TableName("assistant_thinking")
public class AssistantThinkingEntity {
    @TableId(type = IdType.AUTO)
    private Long id;
    private Long projectId;
    private Long userMessageId;
    private String content;
    private LocalDateTime createdAt;
    private LocalDateTime updatedAt;
} 