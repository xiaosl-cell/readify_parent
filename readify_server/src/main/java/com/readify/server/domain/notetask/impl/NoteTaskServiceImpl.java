package com.readify.server.domain.notetask.impl;

import com.readify.server.domain.notetask.model.NoteTask;
import com.readify.server.domain.notetask.NoteTaskService;
import com.readify.server.domain.notetask.repository.NoteTaskRepository;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;
import java.util.Optional;

/**
 * 笔记任务领域服务实现类
 */
@Service
public class NoteTaskServiceImpl implements NoteTaskService {
    
    private final NoteTaskRepository noteTaskRepository;
    
    @Autowired
    public NoteTaskServiceImpl(NoteTaskRepository noteTaskRepository) {
        this.noteTaskRepository = noteTaskRepository;
    }
    
    @Override
    @Transactional
    public NoteTask createNoteTask(NoteTask noteTask) {
        // 设置创建和更新时间
        long currentTime = System.currentTimeMillis();
        noteTask.setCreateTime(currentTime);
        noteTask.setUpdateTime(currentTime);
        noteTask.setDeleted(false);
        
        return noteTaskRepository.save(noteTask);
    }
    
    @Override
    public Optional<NoteTask> getNoteTaskById(Long id) {
        return noteTaskRepository.findById(id);
    }
    
    @Override
    public List<NoteTask> getNoteTasksByUserId(Long userId) {
        return noteTaskRepository.findByUserId(userId);
    }
    
    @Override
    public List<NoteTask> getNoteTasksByProjectId(Long projectId) {
        return noteTaskRepository.findByProjectId(projectId);
    }
    
    @Override
    public List<NoteTask> getNoteTasksByMindMapId(Long mindMapId) {
        return noteTaskRepository.findByMindMapId(mindMapId);
    }
    
    @Override
    public List<NoteTask> getNoteTasksByFileId(Long fileId) {
        return noteTaskRepository.findByFileId(fileId);
    }
    
    @Override
    @Transactional
    public NoteTask updateNoteTask(NoteTask noteTask) {
        // 更新更新时间
        noteTask.setUpdateTime(System.currentTimeMillis());
        return noteTaskRepository.update(noteTask);
    }
    
    @Override
    @Transactional
    public NoteTask updateNoteTaskStatus(Long id, String status) {
        // 先获取笔记任务
        Optional<NoteTask> optionalNoteTask = noteTaskRepository.findById(id);
        if (optionalNoteTask.isPresent()) {
            NoteTask noteTask = optionalNoteTask.get();
            noteTask.setStatus(status);
            noteTask.setUpdateTime(System.currentTimeMillis());
            return noteTaskRepository.update(noteTask);
        }
        return null;
    }
    
    @Override
    @Transactional
    public NoteTask updateNoteTaskResult(Long id, String result) {
        // 先获取笔记任务
        Optional<NoteTask> optionalNoteTask = noteTaskRepository.findById(id);
        if (optionalNoteTask.isPresent()) {
            NoteTask noteTask = optionalNoteTask.get();
            noteTask.setResult(result);
            noteTask.setUpdateTime(System.currentTimeMillis());
            return noteTaskRepository.update(noteTask);
        }
        return null;
    }
    
    @Override
    @Transactional
    public void deleteNoteTask(Long id) {
        noteTaskRepository.deleteById(id);
    }
} 