package com.readify.server.domain.auth.service;

import com.readify.server.domain.auth.model.AuthUser;
import com.readify.server.domain.auth.model.LoginResult;

public interface AuthService {
    /**
     * 用户注册
     *
     * @param username 用户名
     * @param password 密码
     * @return 注册成功的用户信息
     */
    AuthUser register(String username, String password);

    /**
     * 用户登录
     *
     * @param username 用户名
     * @param password 密码
     * @return 登录成功的用户信息和token
     */
    LoginResult login(String username, String password);
} 