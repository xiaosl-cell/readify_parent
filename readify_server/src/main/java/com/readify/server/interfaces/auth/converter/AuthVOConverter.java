package com.readify.server.interfaces.auth.converter;

import com.readify.server.domain.auth.model.AuthUser;
import com.readify.server.interfaces.auth.vo.LoginVO;
import org.mapstruct.Mapper;
import org.mapstruct.MappingTarget;
import org.mapstruct.factory.Mappers;

@Mapper
public interface AuthVOConverter {
    AuthVOConverter INSTANCE = Mappers.getMapper(AuthVOConverter.class);

    void updateLoginVO(AuthUser user, @MappingTarget LoginVO loginVO);
} 