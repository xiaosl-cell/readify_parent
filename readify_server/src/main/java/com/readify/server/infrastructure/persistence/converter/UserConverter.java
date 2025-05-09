package com.readify.server.infrastructure.persistence.converter;

import com.readify.server.domain.user.model.User;
import com.readify.server.infrastructure.persistence.entity.UserEntity;
import org.mapstruct.Mapper;
import org.mapstruct.factory.Mappers;

@Mapper
public interface UserConverter {
    UserConverter INSTANCE = Mappers.getMapper(UserConverter.class);

    UserEntity toEntity(User user);

    User toDomain(UserEntity entity);
}