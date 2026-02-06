package com.readify.server.infrastructure.persistence.repository;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.readify.server.domain.auth.repository.RbacRepository;
import com.readify.server.infrastructure.persistence.entity.PermissionEntity;
import com.readify.server.infrastructure.persistence.entity.RoleEntity;
import com.readify.server.infrastructure.persistence.entity.RolePermissionEntity;
import com.readify.server.infrastructure.persistence.entity.UserEntity;
import com.readify.server.infrastructure.persistence.entity.UserRoleEntity;
import com.readify.server.infrastructure.persistence.mapper.PermissionMapper;
import com.readify.server.infrastructure.persistence.mapper.RoleMapper;
import com.readify.server.infrastructure.persistence.mapper.RolePermissionMapper;
import com.readify.server.infrastructure.persistence.mapper.UserMapper;
import com.readify.server.infrastructure.persistence.mapper.UserRoleMapper;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Repository;

import java.util.Collections;
import java.util.List;
import java.util.Optional;
import java.util.stream.Collectors;

@Repository
@RequiredArgsConstructor
public class RbacRepositoryImpl implements RbacRepository {
    private final RoleMapper roleMapper;
    private final PermissionMapper permissionMapper;
    private final UserRoleMapper userRoleMapper;
    private final RolePermissionMapper rolePermissionMapper;
    private final UserMapper userMapper;

    @Override
    public List<String> findRoleCodesByUserId(Long userId) {
        List<UserRoleEntity> userRoles = userRoleMapper.selectList(
                new LambdaQueryWrapper<UserRoleEntity>().eq(UserRoleEntity::getUserId, userId));
        if (userRoles.isEmpty()) {
            return Collections.emptyList();
        }
        List<Long> roleIds = userRoles.stream().map(UserRoleEntity::getRoleId).distinct().collect(Collectors.toList());
        List<RoleEntity> roles = roleMapper.selectBatchIds(roleIds);
        return roles.stream()
                .filter(role -> Boolean.TRUE.equals(role.getEnabled()))
                .map(RoleEntity::getCode)
                .collect(Collectors.toList());
    }

    @Override
    public List<String> findPermissionCodesByUserId(Long userId) {
        List<UserRoleEntity> userRoles = userRoleMapper.selectList(
                new LambdaQueryWrapper<UserRoleEntity>().eq(UserRoleEntity::getUserId, userId));
        if (userRoles.isEmpty()) {
            return Collections.emptyList();
        }
        List<Long> roleIds = userRoles.stream().map(UserRoleEntity::getRoleId).distinct().collect(Collectors.toList());
        List<RolePermissionEntity> rolePermissions = rolePermissionMapper.selectList(
                new LambdaQueryWrapper<RolePermissionEntity>().in(RolePermissionEntity::getRoleId, roleIds));
        if (rolePermissions.isEmpty()) {
            return Collections.emptyList();
        }
        List<Long> permissionIds = rolePermissions.stream()
                .map(RolePermissionEntity::getPermissionId)
                .distinct()
                .collect(Collectors.toList());
        List<PermissionEntity> permissions = permissionMapper.selectBatchIds(permissionIds);
        return permissions.stream()
                .filter(permission -> Boolean.TRUE.equals(permission.getEnabled()))
                .map(PermissionEntity::getCode)
                .collect(Collectors.toList());
    }

    @Override
    public Optional<Long> findRoleIdByCode(String roleCode) {
        RoleEntity roleEntity = roleMapper.selectOne(new LambdaQueryWrapper<RoleEntity>()
                .eq(RoleEntity::getCode, roleCode)
                .eq(RoleEntity::getEnabled, true)
                .last("LIMIT 1"));
        return Optional.ofNullable(roleEntity).map(RoleEntity::getId);
    }

    @Override
    public boolean existsUserRole(Long userId, Long roleId) {
        return userRoleMapper.selectCount(new LambdaQueryWrapper<UserRoleEntity>()
                .eq(UserRoleEntity::getUserId, userId)
                .eq(UserRoleEntity::getRoleId, roleId)) > 0;
    }

    @Override
    public void saveUserRole(Long userId, Long roleId) {
        UserRoleEntity userRoleEntity = new UserRoleEntity();
        long now = System.currentTimeMillis();
        userRoleEntity.setUserId(userId);
        userRoleEntity.setRoleId(roleId);
        userRoleEntity.setCreateTime(now);
        userRoleEntity.setUpdateTime(now);
        userRoleEntity.setDeleted(false);
        userRoleMapper.insert(userRoleEntity);
    }

    @Override
    public List<Long> findAllUserIds() {
        return userMapper.selectList(new LambdaQueryWrapper<UserEntity>().select(UserEntity::getId))
                .stream()
                .map(UserEntity::getId)
                .collect(Collectors.toList());
    }
}

