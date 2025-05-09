package com.readify.server.infrastructure.persistence.repository;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.core.conditions.update.LambdaUpdateWrapper;
import com.readify.server.domain.mind_map.model.MindMapNode;
import com.readify.server.domain.mind_map.repository.MindMapNodeRepository;
import com.readify.server.infrastructure.persistence.converter.MindMapNodeConverter;
import com.readify.server.infrastructure.persistence.entity.MindMapNodeEntity;
import com.readify.server.infrastructure.persistence.mapper.MindMapNodeMapper;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Repository;
import org.springframework.transaction.annotation.Transactional;

import java.util.ArrayList;
import java.util.List;
import java.util.Optional;
import java.util.stream.Collectors;

@Repository
@RequiredArgsConstructor
public class MindMapNodeRepositoryImpl implements MindMapNodeRepository {
    private final MindMapNodeMapper mindMapNodeMapper;
    private final MindMapNodeConverter mindMapNodeConverter = MindMapNodeConverter.INSTANCE;

    @Override
    public MindMapNode save(MindMapNode node) {
        MindMapNodeEntity entity = mindMapNodeConverter.toEntity(node);
        if (entity.getId() == null) {
            mindMapNodeMapper.insert(entity);
        } else {
            mindMapNodeMapper.updateById(entity);
        }
        return mindMapNodeConverter.toDomain(entity);
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public List<MindMapNode> batchSave(List<MindMapNode> nodes) {
        List<MindMapNode> result = new ArrayList<>(nodes.size());
        for (MindMapNode node : nodes) {
            result.add(save(node));
        }
        return result;
    }

    @Override
    public Optional<MindMapNode> findById(Long id) {
        return Optional.ofNullable(mindMapNodeMapper.selectById(id))
                .map(mindMapNodeConverter::toDomain);
    }

    @Override
    public List<MindMapNode> findByFileId(Long fileId) {
        LambdaQueryWrapper<MindMapNodeEntity> queryWrapper = new LambdaQueryWrapper<>();
        queryWrapper.eq(MindMapNodeEntity::getFileId, fileId)
                    .orderByAsc(MindMapNodeEntity::getLevel)
                    .orderByAsc(MindMapNodeEntity::getSequence);
        return mindMapNodeMapper.selectList(queryWrapper).stream()
                .map(mindMapNodeConverter::toDomain)
                .collect(Collectors.toList());
    }
    
    @Override
    public List<MindMapNode> findByMindMapId(Long mindMapId) {
        LambdaQueryWrapper<MindMapNodeEntity> queryWrapper = new LambdaQueryWrapper<>();
        queryWrapper.eq(MindMapNodeEntity::getMindMapId, mindMapId)
                    .orderByAsc(MindMapNodeEntity::getLevel)
                    .orderByAsc(MindMapNodeEntity::getSequence);
        return mindMapNodeMapper.selectList(queryWrapper).stream()
                .map(mindMapNodeConverter::toDomain)
                .collect(Collectors.toList());
    }

    @Override
    public List<MindMapNode> findByParentId(Long parentId) {
        LambdaQueryWrapper<MindMapNodeEntity> queryWrapper = new LambdaQueryWrapper<>();
        queryWrapper.eq(MindMapNodeEntity::getParentId, parentId)
                    .orderByAsc(MindMapNodeEntity::getSequence);
        return mindMapNodeMapper.selectList(queryWrapper).stream()
                .map(mindMapNodeConverter::toDomain)
                .collect(Collectors.toList());
    }

    @Override
    public Optional<MindMapNode> findRootNodeByFileId(Long fileId) {
        LambdaQueryWrapper<MindMapNodeEntity> queryWrapper = new LambdaQueryWrapper<>();
        queryWrapper.eq(MindMapNodeEntity::getFileId, fileId)
                    .isNull(MindMapNodeEntity::getParentId)
                    .eq(MindMapNodeEntity::getLevel, 0);
        return Optional.ofNullable(mindMapNodeMapper.selectOne(queryWrapper))
                .map(mindMapNodeConverter::toDomain);
    }
    
    @Override
    public Optional<MindMapNode> findRootNodeByMindMapId(Long mindMapId) {
        LambdaQueryWrapper<MindMapNodeEntity> queryWrapper = new LambdaQueryWrapper<>();
        queryWrapper.eq(MindMapNodeEntity::getMindMapId, mindMapId)
                    .isNull(MindMapNodeEntity::getParentId)
                    .eq(MindMapNodeEntity::getLevel, 0);
        return Optional.ofNullable(mindMapNodeMapper.selectOne(queryWrapper))
                .map(mindMapNodeConverter::toDomain);
    }

    @Override
    public boolean deleteById(Long id) {
        return mindMapNodeMapper.deleteById(id) > 0;
    }

    @Override
    public int deleteByFileId(Long fileId) {
        LambdaQueryWrapper<MindMapNodeEntity> queryWrapper = new LambdaQueryWrapper<>();
        queryWrapper.eq(MindMapNodeEntity::getFileId, fileId);
        return mindMapNodeMapper.delete(queryWrapper);
    }
    
    @Override
    public int deleteByMindMapId(Long mindMapId) {
        LambdaQueryWrapper<MindMapNodeEntity> queryWrapper = new LambdaQueryWrapper<>();
        queryWrapper.eq(MindMapNodeEntity::getMindMapId, mindMapId);
        return mindMapNodeMapper.delete(queryWrapper);
    }

    @Override
    public boolean updateSequence(Long id, Integer sequence) {
        LambdaUpdateWrapper<MindMapNodeEntity> updateWrapper = new LambdaUpdateWrapper<>();
        updateWrapper.eq(MindMapNodeEntity::getId, id)
                    .set(MindMapNodeEntity::getSequence, sequence)
                    .set(MindMapNodeEntity::getUpdatedTime, System.currentTimeMillis());
        return mindMapNodeMapper.update(null, updateWrapper) > 0;
    }
} 