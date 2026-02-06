package com.readify.server.domain.auth.service.impl;

import com.readify.server.domain.auth.repository.RbacRepository;
import com.readify.server.domain.auth.service.RbacService;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.Collection;
import java.util.Collections;
import java.util.List;
import java.util.Locale;
import java.util.stream.Collectors;

@Service
@RequiredArgsConstructor
public class RbacServiceImpl implements RbacService {
    private static final String DEFAULT_ROLE_CODE = "ROLE_USER";
    private final RbacRepository rbacRepository;

    @Override
    public Collection<String> getRoleAuthorities(Long userId) {
        List<String> roleCodes = rbacRepository.findRoleCodesByUserId(userId);
        if (roleCodes.isEmpty()) {
            return Collections.singleton(DEFAULT_ROLE_CODE);
        }
        return roleCodes.stream()
                .map(code -> code.toUpperCase(Locale.ROOT))
                .collect(Collectors.toSet());
    }

    @Override
    public Collection<String> getPermissionAuthorities(Long userId) {
        return rbacRepository.findPermissionCodesByUserId(userId).stream()
                .map(code -> code.toUpperCase(Locale.ROOT))
                .collect(Collectors.toSet());
    }

    @Override
    @Transactional
    public void grantDefaultRoleForUser(Long userId) {
        Long roleId = rbacRepository.findRoleIdByCode(DEFAULT_ROLE_CODE).orElse(null);
        if (roleId == null) {
            return;
        }
        if (!rbacRepository.existsUserRole(userId, roleId)) {
            rbacRepository.saveUserRole(userId, roleId);
        }
    }

    @Override
    @Transactional
    public void ensureDefaultRoleForExistingUsers() {
        List<Long> allUserIds = rbacRepository.findAllUserIds();
        for (Long userId : allUserIds) {
            grantDefaultRoleForUser(userId);
        }
    }
}

