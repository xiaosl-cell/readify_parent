package com.readify.server.infrastructure.persistence.converter;

import com.readify.server.domain.file.model.File;
import com.readify.server.infrastructure.persistence.entity.FileEntity;
import org.mapstruct.Mapper;
import org.mapstruct.factory.Mappers;

@Mapper
public interface FileConverter {
    FileConverter INSTANCE = Mappers.getMapper(FileConverter.class);

    FileEntity toEntity(File file);

    File toDomain(FileEntity entity);
} 