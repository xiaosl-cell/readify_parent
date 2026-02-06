package com.readify.server.domain.auth.repository;

import java.util.List;
import java.util.Optional;

public interface RbacRepository {
    List<String> findRoleCodesByUserId(Long userId);

    List<String> findPermissionCodesByUserId(Long userId);

    Optional<Long> findRoleIdByCode(String roleCode);

    boolean existsUserRole(Long userId, Long roleId);

    void saveUserRole(Long userId, Long roleId);

    List<Long> findAllUserIds();
}

