package com.readify.server.domain.auth.repository;

import com.readify.server.domain.auth.model.AuthUser;

public interface AuthUserRepository {
    /**
     * 保存认证用户信息
     *
     * @param authUser 认证用户信息
     * @return 保存后的认证用户信息
     */
    AuthUser save(AuthUser authUser);

    /**
     * 根据用户名查找认证用户信息
     *
     * @param username 用户名
     * @return 认证用户信息
     */
    AuthUser findByUsername(String username);

    /**
     * 检查用户名是否已存在
     *
     * @param username 用户名
     * @return true 如果用户名已存在，否则返回 false
     */
    boolean existsByUsername(String username);
} 