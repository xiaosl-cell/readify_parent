package com.readify.server.domain.auth.service.impl;

import com.readify.server.domain.auth.model.Permission;
import com.readify.server.domain.auth.model.Role;
import com.readify.server.domain.auth.repository.RbacRepository;
import com.readify.server.domain.auth.service.RbacManageService;
import com.readify.server.infrastructure.common.PageResult;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.stream.Collectors;

@Service
@RequiredArgsConstructor
public class RbacManageServiceImpl implements RbacManageService {
    private final RbacRepository rbacRepository;

    @Override
    @Transactional
    public Role createRole(Role role) {
        if (role.getEnabled() == null) {
            role.setEnabled(true);
        }
        return rbacRepository.saveRole(role);
    }

    @Override
    @Transactional
    public Role updateRole(Role role) {
        return rbacRepository.updateRole(role);
    }

    @Override
    @Transactional
    public void deleteRole(Long roleId) {
        rbacRepository.deleteRolePermissionsByRoleId(roleId);
        rbacRepository.deleteRole(roleId);
    }

    @Override
    public Role getRoleById(Long roleId) {
        return rbacRepository.findRoleById(roleId)
                .orElseThrow(() -> new RuntimeException("Role not found: " + roleId));
    }

    @Override
    public PageResult<Role> getRolesPage(int page, int size, String keyword) {
        List<Role> roles = rbacRepository.findRolesPage(page, size, keyword);
        long total = rbacRepository.countRoles(keyword);
        return PageResult.of(roles, total, page, size);
    }

    @Override
    public List<Role> getAllRoles() {
        return rbacRepository.findAllRoles();
    }

    @Override
    @Transactional
    public Permission createPermission(Permission permission) {
        if (permission.getEnabled() == null) {
            permission.setEnabled(true);
        }
        return rbacRepository.savePermission(permission);
    }

    @Override
    @Transactional
    public Permission updatePermission(Permission permission) {
        return rbacRepository.updatePermission(permission);
    }

    @Override
    @Transactional
    public void deletePermission(Long permissionId) {
        rbacRepository.deletePermission(permissionId);
    }

    @Override
    public Permission getPermissionById(Long permissionId) {
        return rbacRepository.findPermissionById(permissionId)
                .orElseThrow(() -> new RuntimeException("Permission not found: " + permissionId));
    }

    @Override
    public PageResult<Permission> getPermissionsPage(int page, int size, String keyword) {
        List<Permission> permissions = rbacRepository.findPermissionsPage(page, size, keyword);
        long total = rbacRepository.countPermissions(keyword);
        return PageResult.of(permissions, total, page, size);
    }

    @Override
    public List<Permission> getAllPermissions() {
        return rbacRepository.findAllPermissions();
    }

    @Override
    public Map<String, List<Permission>> getPermissionTree() {
        List<Permission> allPermissions = rbacRepository.findAllPermissions();
        return allPermissions.stream()
                .collect(Collectors.groupingBy(
                        p -> p.getModule() != null ? p.getModule() : "OTHER",
                        LinkedHashMap::new,
                        Collectors.toList()
                ));
    }

    @Override
    @Transactional
    public void assignRolesToUser(Long userId, List<Long> roleIds) {
        rbacRepository.deleteUserRolesByUserId(userId);
        for (Long roleId : roleIds) {
            if (!rbacRepository.existsUserRole(userId, roleId)) {
                rbacRepository.saveUserRole(userId, roleId);
            }
        }
    }

    @Override
    public List<Role> getRolesByUserId(Long userId) {
        return rbacRepository.findRolesByUserId(userId);
    }

    @Override
    @Transactional
    public void assignPermissionsToRole(Long roleId, List<Long> permissionIds) {
        rbacRepository.deleteRolePermissionsByRoleId(roleId);
        for (Long permissionId : permissionIds) {
            if (!rbacRepository.existsRolePermission(roleId, permissionId)) {
                rbacRepository.saveRolePermission(roleId, permissionId);
            }
        }
    }

    @Override
    public List<Permission> getPermissionsByRoleId(Long roleId) {
        return rbacRepository.findPermissionsByRoleId(roleId);
    }

    @Override
    public long countUsers() {
        return rbacRepository.findAllUserIds().size();
    }

    @Override
    public long countRoles() {
        return rbacRepository.countRoles(null);
    }

    @Override
    public long countPermissions() {
        return rbacRepository.countPermissions(null);
    }
}
