package com.readify.server.domain.project.repository;

import com.readify.server.domain.project.model.Project;

import java.util.List;
import java.util.Optional;

public interface ProjectRepository {
    /**
     * 保存工程信息
     *
     * @param project 工程信息
     * @return 保存后的工程信息
     */
    Project save(Project project);

    /**
     * 根据ID查找工程
     *
     * @param id 工程ID
     * @return 工程信息
     */
    Optional<Project> findById(Long id);

    /**
     * 根据名称查找工程
     *
     * @param name 工程名称
     * @return 工程信息
     */
    Optional<Project> findByName(String name);

    /**
     * 获取所有工程
     *
     * @return 工程列表
     */
    List<Project> findAll();

    /**
     * 获取用户的所有工程
     *
     * @param userId 用户ID
     * @return 工程列表
     */
    List<Project> findByUserId(Long userId);

    /**
     * 根据ID删除工程
     *
     * @param id 工程ID
     */
    void deleteById(Long id);

    /**
     * 检查工程名称是否已存在
     *
     * @param name 工程名称
     * @param userId 用户ID
     * @return true 如果名称已存在，否则返回 false
     */
    boolean existsByNameAndUserId(String name, Long userId);
} 