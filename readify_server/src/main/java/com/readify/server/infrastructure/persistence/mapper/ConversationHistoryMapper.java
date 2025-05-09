package com.readify.server.infrastructure.persistence.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.readify.server.infrastructure.persistence.entity.ConversationHistoryEntity;
import org.apache.ibatis.annotations.Mapper;

@Mapper
public interface ConversationHistoryMapper extends BaseMapper<ConversationHistoryEntity> {
} 