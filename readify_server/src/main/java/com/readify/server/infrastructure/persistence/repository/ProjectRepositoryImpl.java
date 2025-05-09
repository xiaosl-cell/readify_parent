package com.readify.server.infrastructure.persistence.repository;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.readify.server.domain.project.model.Project;
import com.readify.server.domain.project.repository.ProjectRepository;
import com.readify.server.infrastructure.persistence.entity.ProjectEntity;
import com.readify.server.infrastructure.persistence.converter.ProjectConverter;
import com.readify.server.infrastructure.persistence.mapper.ProjectMapper;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Repository;

import java.util.List;
import java.util.Optional;
import java.util.stream.Collectors;

@Repository
@RequiredArgsConstructor
public class ProjectRepositoryImpl implements ProjectRepository {
    private final ProjectMapper projectMapper;
    private final ProjectConverter projectConverter = ProjectConverter.INSTANCE;

    @Override
    public Project save(Project project) {
        ProjectEntity entity = projectConverter.toEntity(project);
        if (project.getId() == null) {
            projectMapper.insert(entity);
        } else {
            projectMapper.updateById(entity);
        }
        return projectConverter.toDomain(entity);
    }

    @Override
    public Optional<Project> findById(Long id) {
        return Optional.ofNullable(projectMapper.selectById(id))
                .map(projectConverter::toDomain);
    }

    @Override
    public Optional<Project> findByName(String name) {
        LambdaQueryWrapper<ProjectEntity> queryWrapper = new LambdaQueryWrapper<>();
        queryWrapper.eq(ProjectEntity::getName, name);
        return Optional.ofNullable(projectMapper.selectOne(queryWrapper))
                .map(projectConverter::toDomain);
    }

    @Override
    public List<Project> findAll() {
        return projectMapper.selectList(null).stream()
                .map(projectConverter::toDomain)
                .collect(Collectors.toList());
    }

    @Override
    public List<Project> findByUserId(Long userId) {
        LambdaQueryWrapper<ProjectEntity> queryWrapper = new LambdaQueryWrapper<>();
        queryWrapper.eq(ProjectEntity::getUserId, userId);
        return projectMapper.selectList(queryWrapper).stream()
                .map(projectConverter::toDomain)
                .collect(Collectors.toList());
    }

    @Override
    public void deleteById(Long id) {
        projectMapper.deleteById(id);
    }

    @Override
    public boolean existsByNameAndUserId(String name, Long userId) {
        LambdaQueryWrapper<ProjectEntity> queryWrapper = new LambdaQueryWrapper<>();
        queryWrapper.eq(ProjectEntity::getName, name)
                   .eq(ProjectEntity::getUserId, userId);
        return projectMapper.selectCount(queryWrapper) > 0;
    }
} 