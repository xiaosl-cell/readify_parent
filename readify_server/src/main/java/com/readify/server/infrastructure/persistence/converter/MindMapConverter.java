package com.readify.server.infrastructure.persistence.converter;

import com.readify.server.domain.mind_map.model.MindMap;
import com.readify.server.infrastructure.persistence.entity.MindMapEntity;
import org.mapstruct.Mapper;
import org.mapstruct.factory.Mappers;

@Mapper
public interface MindMapConverter {
    MindMapConverter INSTANCE = Mappers.getMapper(MindMapConverter.class);

    MindMapEntity toEntity(MindMap mindMap);

    MindMap toDomain(MindMapEntity entity);
} 