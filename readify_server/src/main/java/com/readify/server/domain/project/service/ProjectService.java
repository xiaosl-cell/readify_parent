package com.readify.server.domain.project.service;

import com.readify.server.domain.project.model.Project;

import java.util.List;

public interface ProjectService {
    /**
     * 创建新工程
     *
     * @param project 工程信息
     * @param userId 用户ID
     * @return 创建后的工程信息
     */
    Project createProject(Project project, Long userId);

    /**
     * 更新工程信息
     *
     * @param project 工程信息
     * @param userId 用户ID
     * @return 更新后的工程信息
     */
    Project updateProject(Project project, Long userId);

    /**
     * 删除工程
     *
     * @param id 工程ID
     * @param userId 用户ID
     */
    void deleteProject(Long id, Long userId);

    /**
     * 根据ID获取工程信息
     *
     * @param id 工程ID
     * @param userId 用户ID
     * @return 工程信息
     */
    Project getProjectById(Long id, Long userId);

    /**
     * 根据名称获取工程信息
     *
     * @param name 工程名称
     * @param userId 用户ID
     * @return 工程信息
     */
    Project getProjectByName(String name, Long userId);

    /**
     * 获取所有工程
     *
     * @return 工程列表
     */
    List<Project> getAllProjects();

    /**
     * 获取用户的所有工程
     *
     * @param userId 用户ID
     * @return 工程列表
     */
    List<Project> getUserProjects(Long userId);

    /**
     * 检查工程名称是否已存在
     *
     * @param name 工程名称
     * @param userId 用户ID
     * @return true 如果名称已存在，否则返回 false
     */
    boolean isProjectNameExists(String name, Long userId);
} 