package com.readify.server.infrastructure.security;

import com.readify.server.infrastructure.common.exception.UnauthorizedException;
import lombok.extern.slf4j.Slf4j;

@Slf4j
public class SecurityUtils {
    private static final ThreadLocal<UserInfo> userInfoHolder = new ThreadLocal<>();

    /**
     * 设置当前用户信息
     *
     * @param userInfo 用户信息
     */
    public static void setCurrentUser(UserInfo userInfo) {
        userInfoHolder.set(userInfo);
    }

    /**
     * 获取当前用户信息
     *
     * @return 用户信息
     * @throws UnauthorizedException 如果用户未登录
     */
    public static UserInfo getCurrentUser() {
        UserInfo userInfo = userInfoHolder.get();
        if (userInfo == null) {
            throw new UnauthorizedException("用户未登录");
        }
        return userInfo;
    }

    /**
     * 获取当前用户ID
     *
     * @return 用户ID
     * @throws UnauthorizedException 如果用户未登录
     */
    public static Long getCurrentUserId() {
        return getCurrentUser().getId();
    }

    /**
     * 获取当前用户名
     *
     * @return 用户名
     * @throws UnauthorizedException 如果用户未登录
     */
    public static String getCurrentUsername() {
        return getCurrentUser().getUsername();
    }

    /**
     * 清除当前用户信息
     */
    public static void clearCurrentUser() {
        userInfoHolder.remove();
    }
} 