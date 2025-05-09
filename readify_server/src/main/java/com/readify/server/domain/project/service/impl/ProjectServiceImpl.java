package com.readify.server.domain.project.service.impl;

import com.readify.server.domain.project.model.Project;
import com.readify.server.domain.project.repository.ProjectRepository;
import com.readify.server.domain.project.service.ProjectService;
import com.readify.server.infrastructure.common.exception.BusinessException;
import com.readify.server.infrastructure.common.exception.ForbiddenException;
import com.readify.server.infrastructure.common.exception.NotFoundException;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;

import java.util.List;

@Service
@RequiredArgsConstructor
public class ProjectServiceImpl implements ProjectService {
    private final ProjectRepository projectRepository;

    @Override
    public Project createProject(Project project, Long userId) {
        if (projectRepository.existsByNameAndUserId(project.getName(), userId)) {
            throw new BusinessException("工程名称已存在");
        }
        project.setUserId(userId);
        project.setCreateTime(System.currentTimeMillis());
        project.setUpdateTime(System.currentTimeMillis());
        return projectRepository.save(project);
    }

    @Override
    public Project updateProject(Project project, Long userId) {
        Project existingProject = getProjectById(project.getId(), userId);
        // 如果名称发生变化，需要检查新名称是否已存在
        if (!existingProject.getName().equals(project.getName()) 
            && projectRepository.existsByNameAndUserId(project.getName(), userId)) {
            throw new BusinessException("工程名称已存在");
        }
        project.setUserId(userId);
        project.setCreateTime(existingProject.getCreateTime());
        project.setUpdateTime(System.currentTimeMillis());
        return projectRepository.save(project);
    }

    @Override
    public void deleteProject(Long id, Long userId) {
        Project project = projectRepository.findById(id)
                .orElseThrow(() -> new NotFoundException("工程不存在"));
        if (!project.getUserId().equals(userId)) {
            throw new ForbiddenException("无权操作此工程");
        }
        projectRepository.deleteById(id);
    }

    @Override
    public Project getProjectById(Long id, Long userId) {
        Project project = projectRepository.findById(id)
                .orElseThrow(() -> new NotFoundException("工程不存在"));
        if (!project.getUserId().equals(userId)) {
            throw new ForbiddenException("无权访问此工程");
        }
        return project;
    }

    @Override
    public Project getProjectByName(String name, Long userId) {
        return projectRepository.findByName(name)
                .filter(project -> project.getUserId().equals(userId))
                .orElseThrow(() -> new NotFoundException("工程不存在"));
    }

    @Override
    public List<Project> getAllProjects() {
        return projectRepository.findAll();
    }

    @Override
    public List<Project> getUserProjects(Long userId) {
        return projectRepository.findByUserId(userId);
    }

    @Override
    public boolean isProjectNameExists(String name, Long userId) {
        return projectRepository.existsByNameAndUserId(name, userId);
    }
} 