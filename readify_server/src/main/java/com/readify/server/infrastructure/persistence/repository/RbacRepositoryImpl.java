package com.readify.server.infrastructure.persistence.repository;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.readify.server.domain.auth.model.Permission;
import com.readify.server.domain.auth.model.Role;
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
import org.springframework.util.StringUtils;

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

    // Role CRUD implementations
    @Override
    public Role saveRole(Role role) {
        RoleEntity entity = toRoleEntity(role);
        long now = System.currentTimeMillis();
        entity.setCreateTime(now);
        entity.setUpdateTime(now);
        entity.setDeleted(false);
        roleMapper.insert(entity);
        role.setId(entity.getId());
        role.setCreateTime(now);
        role.setUpdateTime(now);
        return role;
    }

    @Override
    public Role updateRole(Role role) {
        RoleEntity entity = toRoleEntity(role);
        entity.setUpdateTime(System.currentTimeMillis());
        roleMapper.updateById(entity);
        return role;
    }

    @Override
    public void deleteRole(Long roleId) {
        roleMapper.deleteById(roleId);
    }

    @Override
    public Optional<Role> findRoleById(Long roleId) {
        RoleEntity entity = roleMapper.selectById(roleId);
        return Optional.ofNullable(entity).map(this::toRole);
    }

    @Override
    public List<Role> findAllRoles() {
        return roleMapper.selectList(new LambdaQueryWrapper<RoleEntity>()
                        .orderByAsc(RoleEntity::getId))
                .stream()
                .map(this::toRole)
                .collect(Collectors.toList());
    }

    @Override
    public List<Role> findRolesPage(int page, int size, String keyword) {
        LambdaQueryWrapper<RoleEntity> wrapper = new LambdaQueryWrapper<>();
        if (StringUtils.hasText(keyword)) {
            wrapper.and(w -> w.like(RoleEntity::getName, keyword)
                    .or().like(RoleEntity::getCode, keyword));
        }
        wrapper.orderByAsc(RoleEntity::getId);
        Page<RoleEntity> pageResult = roleMapper.selectPage(new Page<>(page, size), wrapper);
        return pageResult.getRecords().stream()
                .map(this::toRole)
                .collect(Collectors.toList());
    }

    @Override
    public long countRoles(String keyword) {
        LambdaQueryWrapper<RoleEntity> wrapper = new LambdaQueryWrapper<>();
        if (StringUtils.hasText(keyword)) {
            wrapper.and(w -> w.like(RoleEntity::getName, keyword)
                    .or().like(RoleEntity::getCode, keyword));
        }
        return roleMapper.selectCount(wrapper);
    }

    // Permission CRUD implementations
    @Override
    public Permission savePermission(Permission permission) {
        PermissionEntity entity = toPermissionEntity(permission);
        long now = System.currentTimeMillis();
        entity.setCreateTime(now);
        entity.setUpdateTime(now);
        entity.setDeleted(false);
        permissionMapper.insert(entity);
        permission.setId(entity.getId());
        permission.setCreateTime(now);
        permission.setUpdateTime(now);
        return permission;
    }

    @Override
    public Permission updatePermission(Permission permission) {
        PermissionEntity entity = toPermissionEntity(permission);
        entity.setUpdateTime(System.currentTimeMillis());
        permissionMapper.updateById(entity);
        return permission;
    }

    @Override
    public void deletePermission(Long permissionId) {
        permissionMapper.deleteById(permissionId);
    }

    @Override
    public Optional<Permission> findPermissionById(Long permissionId) {
        PermissionEntity entity = permissionMapper.selectById(permissionId);
        return Optional.ofNullable(entity).map(this::toPermission);
    }

    @Override
    public List<Permission> findAllPermissions() {
        return permissionMapper.selectList(new LambdaQueryWrapper<PermissionEntity>()
                        .orderByAsc(PermissionEntity::getModule, PermissionEntity::getId))
                .stream()
                .map(this::toPermission)
                .collect(Collectors.toList());
    }

    @Override
    public List<Permission> findPermissionsPage(int page, int size, String keyword) {
        LambdaQueryWrapper<PermissionEntity> wrapper = new LambdaQueryWrapper<>();
        if (StringUtils.hasText(keyword)) {
            wrapper.and(w -> w.like(PermissionEntity::getName, keyword)
                    .or().like(PermissionEntity::getCode, keyword)
                    .or().like(PermissionEntity::getModule, keyword));
        }
        wrapper.orderByAsc(PermissionEntity::getModule, PermissionEntity::getId);
        Page<PermissionEntity> pageResult = permissionMapper.selectPage(new Page<>(page, size), wrapper);
        return pageResult.getRecords().stream()
                .map(this::toPermission)
                .collect(Collectors.toList());
    }

    @Override
    public long countPermissions(String keyword) {
        LambdaQueryWrapper<PermissionEntity> wrapper = new LambdaQueryWrapper<>();
        if (StringUtils.hasText(keyword)) {
            wrapper.and(w -> w.like(PermissionEntity::getName, keyword)
                    .or().like(PermissionEntity::getCode, keyword)
                    .or().like(PermissionEntity::getModule, keyword));
        }
        return permissionMapper.selectCount(wrapper);
    }

    // Association management implementations
    @Override
    public void deleteUserRolesByUserId(Long userId) {
        userRoleMapper.delete(new LambdaQueryWrapper<UserRoleEntity>()
                .eq(UserRoleEntity::getUserId, userId));
    }

    @Override
    public void deleteRolePermissionsByRoleId(Long roleId) {
        rolePermissionMapper.delete(new LambdaQueryWrapper<RolePermissionEntity>()
                .eq(RolePermissionEntity::getRoleId, roleId));
    }

    @Override
    public void saveRolePermission(Long roleId, Long permissionId) {
        RolePermissionEntity entity = new RolePermissionEntity();
        long now = System.currentTimeMillis();
        entity.setRoleId(roleId);
        entity.setPermissionId(permissionId);
        entity.setCreateTime(now);
        entity.setUpdateTime(now);
        entity.setDeleted(false);
        rolePermissionMapper.insert(entity);
    }

    @Override
    public List<Role> findRolesByUserId(Long userId) {
        List<UserRoleEntity> userRoles = userRoleMapper.selectList(
                new LambdaQueryWrapper<UserRoleEntity>().eq(UserRoleEntity::getUserId, userId));
        if (userRoles.isEmpty()) {
            return Collections.emptyList();
        }
        List<Long> roleIds = userRoles.stream()
                .map(UserRoleEntity::getRoleId)
                .distinct()
                .collect(Collectors.toList());
        return roleMapper.selectBatchIds(roleIds).stream()
                .map(this::toRole)
                .collect(Collectors.toList());
    }

    @Override
    public List<Permission> findPermissionsByRoleId(Long roleId) {
        List<RolePermissionEntity> rolePermissions = rolePermissionMapper.selectList(
                new LambdaQueryWrapper<RolePermissionEntity>().eq(RolePermissionEntity::getRoleId, roleId));
        if (rolePermissions.isEmpty()) {
            return Collections.emptyList();
        }
        List<Long> permissionIds = rolePermissions.stream()
                .map(RolePermissionEntity::getPermissionId)
                .distinct()
                .collect(Collectors.toList());
        return permissionMapper.selectBatchIds(permissionIds).stream()
                .map(this::toPermission)
                .collect(Collectors.toList());
    }

    @Override
    public boolean existsRolePermission(Long roleId, Long permissionId) {
        return rolePermissionMapper.selectCount(new LambdaQueryWrapper<RolePermissionEntity>()
                .eq(RolePermissionEntity::getRoleId, roleId)
                .eq(RolePermissionEntity::getPermissionId, permissionId)) > 0;
    }

    // Conversion helpers
    private Role toRole(RoleEntity entity) {
        return Role.builder()
                .id(entity.getId())
                .code(entity.getCode())
                .name(entity.getName())
                .description(entity.getDescription())
                .enabled(entity.getEnabled())
                .createTime(entity.getCreateTime())
                .updateTime(entity.getUpdateTime())
                .build();
    }

    private RoleEntity toRoleEntity(Role role) {
        RoleEntity entity = new RoleEntity();
        entity.setId(role.getId());
        entity.setCode(role.getCode());
        entity.setName(role.getName());
        entity.setDescription(role.getDescription());
        entity.setEnabled(role.getEnabled());
        entity.setCreateTime(role.getCreateTime());
        entity.setUpdateTime(role.getUpdateTime());
        return entity;
    }

    private Permission toPermission(PermissionEntity entity) {
        return Permission.builder()
                .id(entity.getId())
                .code(entity.getCode())
                .name(entity.getName())
                .module(entity.getModule())
                .description(entity.getDescription())
                .enabled(entity.getEnabled())
                .createTime(entity.getCreateTime())
                .updateTime(entity.getUpdateTime())
                .build();
    }

    private PermissionEntity toPermissionEntity(Permission permission) {
        PermissionEntity entity = new PermissionEntity();
        entity.setId(permission.getId());
        entity.setCode(permission.getCode());
        entity.setName(permission.getName());
        entity.setModule(permission.getModule());
        entity.setDescription(permission.getDescription());
        entity.setEnabled(permission.getEnabled());
        entity.setCreateTime(permission.getCreateTime());
        entity.setUpdateTime(permission.getUpdateTime());
        return entity;
    }
}

