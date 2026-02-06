package com.readify.server.domain.auth.repository;

import com.readify.server.domain.auth.model.Permission;
import com.readify.server.domain.auth.model.Role;

import java.util.List;
import java.util.Optional;

public interface RbacRepository {
    List<String> findRoleCodesByUserId(Long userId);

    List<String> findPermissionCodesByUserId(Long userId);

    Optional<Long> findRoleIdByCode(String roleCode);

    boolean existsUserRole(Long userId, Long roleId);

    void saveUserRole(Long userId, Long roleId);

    List<Long> findAllUserIds();

    // Role CRUD
    Role saveRole(Role role);

    Role updateRole(Role role);

    void deleteRole(Long roleId);

    Optional<Role> findRoleById(Long roleId);

    List<Role> findAllRoles();

    List<Role> findRolesPage(int page, int size, String keyword);

    long countRoles(String keyword);

    // Permission CRUD
    Permission savePermission(Permission permission);

    Permission updatePermission(Permission permission);

    void deletePermission(Long permissionId);

    Optional<Permission> findPermissionById(Long permissionId);

    List<Permission> findAllPermissions();

    List<Permission> findPermissionsPage(int page, int size, String keyword);

    long countPermissions(String keyword);

    // Association management
    void deleteUserRolesByUserId(Long userId);

    void deleteRolePermissionsByRoleId(Long roleId);

    void saveRolePermission(Long roleId, Long permissionId);

    List<Role> findRolesByUserId(Long userId);

    List<Permission> findPermissionsByRoleId(Long roleId);

    boolean existsRolePermission(Long roleId, Long permissionId);
}

