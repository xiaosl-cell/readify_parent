package com.readify.server.interfaces.user.converter;

import com.readify.server.domain.user.model.User;
import com.readify.server.interfaces.user.vo.UserVO;
import org.mapstruct.Mapper;
import org.mapstruct.MappingTarget;
import org.mapstruct.factory.Mappers;

import java.util.List;

@Mapper
public interface UserVOConverter {
    UserVOConverter INSTANCE = Mappers.getMapper(UserVOConverter.class);

    UserVO toVO(User user);

    User toDomain(UserVO userVO);

    List<UserVO> toVOList(List<User> users);

    void updateUserVO(User user, @MappingTarget UserVO userVO);
}