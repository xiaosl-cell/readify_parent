package com.readify.server.domain.project.repository;

import com.readify.server.domain.project.model.ProjectFile;

import java.util.List;

public interface ProjectFileRepository {
    /**
     * 保存项目文件关联信息
     *
     * @param projectFile 项目文件关联信息
     * @return 保存后的项目文件关联信息
     */
    ProjectFile save(ProjectFile projectFile);

    /**
     * 根据项目ID查询项目文件关联信息
     *
     * @param projectId 项目ID
     * @return 项目文件关联信息列表
     */
    List<ProjectFile> findByProjectId(Long projectId);
} 