package com.readify.server.domain.notetask.repository;

import com.readify.server.domain.notetask.model.NoteTask;

import java.util.List;
import java.util.Optional;

/**
 * 笔记任务仓储接口
 */
public interface NoteTaskRepository {
    
    /**
     * 保存笔记任务
     *
     * @param noteTask 笔记任务
     * @return 保存后的笔记任务
     */
    NoteTask save(NoteTask noteTask);
    
    /**
     * 根据ID查询笔记任务
     *
     * @param id 笔记任务ID
     * @return 笔记任务
     */
    Optional<NoteTask> findById(Long id);
    
    /**
     * 根据用户ID查询笔记任务列表
     *
     * @param userId 用户ID
     * @return 笔记任务列表
     */
    List<NoteTask> findByUserId(Long userId);
    
    /**
     * 根据项目ID查询笔记任务列表
     *
     * @param projectId 项目ID
     * @return 笔记任务列表
     */
    List<NoteTask> findByProjectId(Long projectId);
    
    /**
     * 根据思维导图ID查询笔记任务列表
     *
     * @param mindMapId 思维导图ID
     * @return 笔记任务列表
     */
    List<NoteTask> findByMindMapId(Long mindMapId);
    
    /**
     * 根据文件ID查询笔记任务列表
     *
     * @param fileId 文件ID
     * @return 笔记任务列表
     */
    List<NoteTask> findByFileId(Long fileId);
    
    /**
     * 更新笔记任务
     *
     * @param noteTask 笔记任务
     * @return 更新后的笔记任务
     */
    NoteTask update(NoteTask noteTask);
    
    /**
     * 根据ID删除笔记任务
     *
     * @param id 笔记任务ID
     */
    void deleteById(Long id);
} 