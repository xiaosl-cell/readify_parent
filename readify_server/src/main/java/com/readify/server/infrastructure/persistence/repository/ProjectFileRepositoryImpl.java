package com.readify.server.infrastructure.persistence.repository;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.readify.server.domain.project.model.ProjectFile;
import com.readify.server.domain.project.repository.ProjectFileRepository;
import com.readify.server.infrastructure.persistence.converter.ProjectFileConverter;
import com.readify.server.infrastructure.persistence.entity.ProjectFileEntity;
import com.readify.server.infrastructure.persistence.mapper.ProjectFileMapper;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Repository;

import java.util.List;
import java.util.stream.Collectors;

@Repository
@RequiredArgsConstructor
public class ProjectFileRepositoryImpl implements ProjectFileRepository {
    private final ProjectFileMapper projectFileMapper;
    private final ProjectFileConverter projectFileConverter = ProjectFileConverter.INSTANCE;

    @Override
    public ProjectFile save(ProjectFile projectFile) {
        ProjectFileEntity entity = projectFileConverter.toEntity(projectFile);
        if (entity.getId() == null) {
            projectFileMapper.insert(entity);
        } else {
            projectFileMapper.updateById(entity);
        }
        return projectFileConverter.toDomain(entity);
    }

    @Override
    public List<ProjectFile> findByProjectId(Long projectId) {
        return projectFileMapper.selectList(new LambdaQueryWrapper<ProjectFileEntity>().eq(ProjectFileEntity::getProjectId, projectId))
                .stream()
                .map(projectFileConverter::toDomain)
                .collect(Collectors.toList());
    }
} 