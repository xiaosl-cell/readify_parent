package com.readify.server.infrastructure.persistence.repository;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.core.conditions.update.LambdaUpdateWrapper;
import com.readify.server.domain.mind_map.model.MindMap;
import com.readify.server.domain.mind_map.repository.MindMapRepository;
import com.readify.server.infrastructure.persistence.converter.MindMapConverter;
import com.readify.server.infrastructure.persistence.entity.MindMapEntity;
import com.readify.server.infrastructure.persistence.mapper.MindMapMapper;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Repository;

import java.util.List;
import java.util.Optional;
import java.util.stream.Collectors;

@Repository
@RequiredArgsConstructor
public class MindMapRepositoryImpl implements MindMapRepository {
    private final MindMapMapper mindMapMapper;
    private final MindMapConverter mindMapConverter = MindMapConverter.INSTANCE;

    @Override
    public MindMap save(MindMap mindMap) {
        MindMapEntity entity = mindMapConverter.toEntity(mindMap);
        if (mindMap.getId() == null) {
            mindMapMapper.insert(entity);
        } else {
            mindMapMapper.updateById(entity);
        }
        return mindMapConverter.toDomain(entity);
    }

    @Override
    public Optional<MindMap> findById(Long id) {
        return Optional.ofNullable(mindMapMapper.selectById(id))
                .map(mindMapConverter::toDomain);
    }

    @Override
    public Optional<MindMap> findByTitleAndUserId(String title, Long userId) {
        LambdaQueryWrapper<MindMapEntity> queryWrapper = new LambdaQueryWrapper<>();
        queryWrapper.eq(MindMapEntity::getTitle, title)
                   .eq(MindMapEntity::getUserId, userId);
        return Optional.ofNullable(mindMapMapper.selectOne(queryWrapper))
                .map(mindMapConverter::toDomain);
    }

    @Override
    public List<MindMap> findByUserId(Long userId) {
        LambdaQueryWrapper<MindMapEntity> queryWrapper = new LambdaQueryWrapper<>();
        queryWrapper.eq(MindMapEntity::getUserId, userId);
        return mindMapMapper.selectList(queryWrapper).stream()
                .map(mindMapConverter::toDomain)
                .collect(Collectors.toList());
    }

    @Override
    public List<MindMap> findByProjectId(Long projectId) {
        LambdaQueryWrapper<MindMapEntity> queryWrapper = new LambdaQueryWrapper<>();
        queryWrapper.eq(MindMapEntity::getProjectId, projectId);
        return mindMapMapper.selectList(queryWrapper).stream()
                .map(mindMapConverter::toDomain)
                .collect(Collectors.toList());
    }

    @Override
    public int deleteByIdAndUserId(Long id, Long userId) {
        // 逻辑删除，将isDeleted字段设置为true
        LambdaUpdateWrapper<MindMapEntity> updateWrapper = new LambdaUpdateWrapper<>();
        updateWrapper.eq(MindMapEntity::getId, id)
                    .eq(MindMapEntity::getUserId, userId)
                    .set(MindMapEntity::getIsDeleted, true);
        return mindMapMapper.update(null, updateWrapper);
    }

    @Override
    public boolean existsByTitleAndProjectIdAndUserId(String title, Long projectId, Long userId) {
        LambdaQueryWrapper<MindMapEntity> queryWrapper = new LambdaQueryWrapper<>();
        queryWrapper.eq(MindMapEntity::getTitle, title)
                   .eq(MindMapEntity::getProjectId, projectId)
                   .eq(MindMapEntity::getUserId, userId);
        return mindMapMapper.selectCount(queryWrapper) > 0;
    }
} 