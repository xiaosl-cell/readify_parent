package com.readify.server.infrastructure.persistence.repository;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.readify.server.domain.auth.model.AuthUser;
import com.readify.server.domain.auth.repository.AuthUserRepository;
import com.readify.server.infrastructure.persistence.entity.UserEntity;
import com.readify.server.infrastructure.persistence.mapper.UserMapper;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Repository;

@Repository
@RequiredArgsConstructor
public class AuthUserRepositoryImpl implements AuthUserRepository {
    private final UserMapper userMapper;

    @Override
    public AuthUser save(AuthUser authUser) {
        UserEntity entity = toEntity(authUser);
        if (authUser.getId() == null) {
            userMapper.insert(entity);
        } else {
            userMapper.updateById(entity);
        }
        return toAuthUser(entity);
    }

    @Override
    public AuthUser findByUsername(String username) {
        LambdaQueryWrapper<UserEntity> queryWrapper = new LambdaQueryWrapper<>();
        queryWrapper.eq(UserEntity::getUsername, username);
        UserEntity entity = userMapper.selectOne(queryWrapper);
        return entity != null ? toAuthUser(entity) : null;
    }

    @Override
    public boolean existsByUsername(String username) {
        LambdaQueryWrapper<UserEntity> queryWrapper = new LambdaQueryWrapper<>();
        queryWrapper.eq(UserEntity::getUsername, username);
        return userMapper.selectCount(queryWrapper) > 0;
    }

    private UserEntity toEntity(AuthUser authUser) {
        if (authUser == null) {
            return null;
        }
        UserEntity entity = new UserEntity();
        entity.setId(authUser.getId());
        entity.setUsername(authUser.getUsername());
        entity.setPassword(authUser.getPassword());
        entity.setEnabled(authUser.getEnabled());
        entity.setCreateTime(authUser.getCreateTime());
        entity.setUpdateTime(authUser.getUpdateTime());
        return entity;
    }

    private AuthUser toAuthUser(UserEntity entity) {
        if (entity == null) {
            return null;
        }
        AuthUser authUser = new AuthUser();
        authUser.setId(entity.getId());
        authUser.setUsername(entity.getUsername());
        authUser.setPassword(entity.getPassword());
        authUser.setEnabled(entity.getEnabled());
        authUser.setCreateTime(entity.getCreateTime());
        authUser.setUpdateTime(entity.getUpdateTime());
        return authUser;
    }
} 