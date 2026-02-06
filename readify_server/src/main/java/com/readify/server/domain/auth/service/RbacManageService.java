package com.readify.server.domain.auth.service;

import com.readify.server.domain.auth.model.Permission;
import com.readify.server.domain.auth.model.Role;
import com.readify.server.infrastructure.common.PageResult;

import java.util.List;
import java.util.Map;

public interface RbacManageService {
    // Role management
    Role createRole(Role role);

    Role updateRole(Role role);

    void deleteRole(Long roleId);

    Role getRoleById(Long roleId);

    PageResult<Role> getRolesPage(int page, int size, String keyword);

    List<Role> getAllRoles();

    // Permission management
    Permission createPermission(Permission permission);

    Permission updatePermission(Permission permission);

    void deletePermission(Long permissionId);

    Permission getPermissionById(Long permissionId);

    PageResult<Permission> getPermissionsPage(int page, int size, String keyword);

    List<Permission> getAllPermissions();

    Map<String, List<Permission>> getPermissionTree();

    // Association management
    void assignRolesToUser(Long userId, List<Long> roleIds);

    List<Role> getRolesByUserId(Long userId);

    void assignPermissionsToRole(Long roleId, List<Long> permissionIds);

    List<Permission> getPermissionsByRoleId(Long roleId);

    // Statistics
    long countUsers();

    long countRoles();

    long countPermissions();
}
