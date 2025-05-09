package com.readify.server.infrastructure.persistence.converter;

import com.readify.server.domain.project.model.ProjectFile;
import com.readify.server.infrastructure.persistence.entity.ProjectFileEntity;
import org.mapstruct.Mapper;
import org.mapstruct.factory.Mappers;

@Mapper
public interface ProjectFileConverter {
    ProjectFileConverter INSTANCE = Mappers.getMapper(ProjectFileConverter.class);

    ProjectFileEntity toEntity(ProjectFile projectFile);

    ProjectFile toDomain(ProjectFileEntity entity);
} 