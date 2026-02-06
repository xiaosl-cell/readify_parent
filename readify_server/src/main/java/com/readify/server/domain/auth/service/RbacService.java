package com.readify.server.domain.auth.service;

import java.util.Collection;

public interface RbacService {
    Collection<String> getRoleAuthorities(Long userId);

    Collection<String> getPermissionAuthorities(Long userId);

    void grantDefaultRoleForUser(Long userId);

    void ensureDefaultRoleForExistingUsers();
}

