package com.readify.server.infrastructure.persistence.repository;

import com.readify.server.domain.notetask.model.NoteTask;
import com.readify.server.domain.notetask.repository.NoteTaskRepository;
import com.readify.server.infrastructure.persistence.converter.NoteTaskConverter;
import com.readify.server.infrastructure.persistence.entity.NoteTaskEntity;
import com.readify.server.infrastructure.persistence.mapper.NoteTaskMapper;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Repository;

import java.util.List;
import java.util.Optional;

/**
 * 笔记任务仓储实现类
 */
@Repository
public class NoteTaskRepositoryImpl implements NoteTaskRepository {
    
    private final NoteTaskMapper noteTaskMapper;
    private final NoteTaskConverter noteTaskConverter;
    
    @Autowired
    public NoteTaskRepositoryImpl(NoteTaskMapper noteTaskMapper, NoteTaskConverter noteTaskConverter) {
        this.noteTaskMapper = noteTaskMapper;
        this.noteTaskConverter = noteTaskConverter;
    }
    
    @Override
    public NoteTask save(NoteTask noteTask) {
        NoteTaskEntity entity = noteTaskConverter.toEntity(noteTask);
        noteTaskMapper.insert(entity);
        return noteTaskConverter.toDomain(entity);
    }
    
    @Override
    public Optional<NoteTask> findById(Long id) {
        NoteTaskEntity entity = noteTaskMapper.selectById(id);
        return Optional.ofNullable(noteTaskConverter.toDomain(entity));
    }
    
    @Override
    public List<NoteTask> findByUserId(Long userId) {
        List<NoteTaskEntity> entities = noteTaskMapper.findByUserId(userId);
        return noteTaskConverter.toDomainList(entities);
    }
    
    @Override
    public List<NoteTask> findByProjectId(Long projectId) {
        List<NoteTaskEntity> entities = noteTaskMapper.findByProjectId(projectId);
        return noteTaskConverter.toDomainList(entities);
    }
    
    @Override
    public List<NoteTask> findByMindMapId(Long mindMapId) {
        List<NoteTaskEntity> entities = noteTaskMapper.findByMindMapId(mindMapId);
        return noteTaskConverter.toDomainList(entities);
    }
    
    @Override
    public List<NoteTask> findByFileId(Long fileId) {
        List<NoteTaskEntity> entities = noteTaskMapper.findByFileId(fileId);
        return noteTaskConverter.toDomainList(entities);
    }
    
    @Override
    public NoteTask update(NoteTask noteTask) {
        NoteTaskEntity entity = noteTaskConverter.toEntity(noteTask);
        noteTaskMapper.updateById(entity);
        return noteTaskConverter.toDomain(entity);
    }
    
    @Override
    public void deleteById(Long id) {
        // 使用逻辑删除，由MyBatis-Plus的@TableLogic注解实现
        noteTaskMapper.deleteById(id);
    }
} 