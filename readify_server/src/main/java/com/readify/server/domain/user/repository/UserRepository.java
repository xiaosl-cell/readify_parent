package com.readify.server.domain.user.repository;

import com.readify.server.domain.user.model.User;

import java.util.List;
import java.util.Optional;

public interface UserRepository {
    /**
     * 保存用户信息
     *
     * @param user 用户信息
     * @return 保存后的用户信息
     */
    User save(User user);

    /**
     * 根据ID查找用户
     *
     * @param id 用户ID
     * @return 用户信息
     */
    Optional<User> findById(Long id);

    /**
     * 根据用户名查找用户
     *
     * @param username 用户名
     * @return 用户信息
     */
    Optional<User> findByUsername(String username);

    /**
     * 获取所有用户
     *
     * @return 用户列表
     */
    List<User> findAll();

    /**
     * 根据ID删除用户
     *
     * @param id 用户ID
     */
    void deleteById(Long id);

    /**
     * 检查用户名是否已存在
     *
     * @param username 用户名
     * @return true 如果用户名已存在，否则返回 false
     */
    boolean existsByUsername(String username);
} 