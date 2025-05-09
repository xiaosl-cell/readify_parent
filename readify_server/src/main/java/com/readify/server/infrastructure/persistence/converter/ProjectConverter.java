package com.readify.server.infrastructure.persistence.converter;

import com.readify.server.domain.project.model.Project;
import com.readify.server.infrastructure.persistence.entity.ProjectEntity;
import org.mapstruct.Mapper;
import org.mapstruct.factory.Mappers;

@Mapper
public interface ProjectConverter {
    ProjectConverter INSTANCE = Mappers.getMapper(ProjectConverter.class);

    ProjectEntity toEntity(Project project);

    Project toDomain(ProjectEntity entity);
} 