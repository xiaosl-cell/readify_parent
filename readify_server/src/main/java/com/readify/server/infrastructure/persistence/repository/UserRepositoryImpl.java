package com.readify.server.infrastructure.persistence.repository;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.readify.server.domain.user.model.User;
import com.readify.server.domain.user.repository.UserRepository;
import com.readify.server.infrastructure.persistence.entity.UserEntity;
import com.readify.server.infrastructure.persistence.converter.UserConverter;
import com.readify.server.infrastructure.persistence.mapper.UserMapper;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Repository;

import java.util.List;
import java.util.Optional;
import java.util.stream.Collectors;

@Repository
@RequiredArgsConstructor
public class UserRepositoryImpl implements UserRepository {
    private final UserMapper userMapper;
    private final UserConverter userConverter = UserConverter.INSTANCE;

    @Override
    public User save(User user) {
        UserEntity entity = userConverter.toEntity(user);
        if (user.getId() == null) {
            userMapper.insert(entity);
        } else {
            userMapper.updateById(entity);
        }
        return userConverter.toDomain(entity);
    }

    @Override
    public Optional<User> findById(Long id) {
        return Optional.ofNullable(userMapper.selectById(id))
                .map(userConverter::toDomain);
    }

    @Override
    public Optional<User> findByUsername(String username) {
        LambdaQueryWrapper<UserEntity> queryWrapper = new LambdaQueryWrapper<>();
        queryWrapper.eq(UserEntity::getUsername, username);
        return Optional.ofNullable(userMapper.selectOne(queryWrapper))
                .map(userConverter::toDomain);
    }

    @Override
    public List<User> findAll() {
        return userMapper.selectList(null).stream()
                .map(userConverter::toDomain)
                .collect(Collectors.toList());
    }

    @Override
    public void deleteById(Long id) {
        userMapper.deleteById(id);
    }

    @Override
    public boolean existsByUsername(String username) {
        LambdaQueryWrapper<UserEntity> queryWrapper = new LambdaQueryWrapper<>();
        queryWrapper.eq(UserEntity::getUsername, username);
        return userMapper.selectCount(queryWrapper) > 0;
    }
}