package com.readify.server.domain.user.service;

import com.readify.server.domain.user.model.User;

import java.util.List;

public interface UserService {
    /**
     * 创建新用户
     *
     * @param user 用户信息
     * @return 创建后的用户信息
     */
    User createUser(User user);

    /**
     * 更新用户信息
     *
     * @param user 用户信息
     * @return 更新后的用户信息
     */
    User updateUser(User user);

    /**
     * 删除用户
     *
     * @param id 用户ID
     */
    void deleteUser(Long id);

    /**
     * 根据ID获取用户信息
     *
     * @param id 用户ID
     * @return 用户信息
     */
    User getUserById(Long id);

    /**
     * 根据用户名获取用户信息
     *
     * @param username 用户名
     * @return 用户信息
     */
    User getUserByUsername(String username);

    /**
     * 获取所有用户
     *
     * @return 用户列表
     */
    List<User> getAllUsers();

    /**
     * 检查用户名是否已存在
     *
     * @param username 用户名
     * @return true 如果用户名已存在，否则返回 false
     */
    boolean isUsernameExists(String username);
} 