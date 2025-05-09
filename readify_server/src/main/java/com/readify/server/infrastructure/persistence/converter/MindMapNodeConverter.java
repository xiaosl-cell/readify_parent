package com.readify.server.infrastructure.persistence.converter;

import com.readify.server.domain.mind_map.model.MindMapNode;
import com.readify.server.infrastructure.persistence.entity.MindMapNodeEntity;
import org.mapstruct.Mapper;
import org.mapstruct.factory.Mappers;

import java.util.List;

@Mapper
public interface MindMapNodeConverter {
    MindMapNodeConverter INSTANCE = Mappers.getMapper(MindMapNodeConverter.class);

    MindMapNodeEntity toEntity(MindMapNode node);

    MindMapNode toDomain(MindMapNodeEntity entity);

    List<MindMapNodeEntity> toEntityList(List<MindMapNode> nodes);

    List<MindMapNode> toDomainList(List<MindMapNodeEntity> entities);
} 