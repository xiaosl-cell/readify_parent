package com.readify.server.domain.notetask;

import com.readify.server.domain.notetask.model.NoteTask;

import java.util.List;
import java.util.Optional;

/**
 * 笔记任务领域服务接口
 */
public interface NoteTaskService {
    
    /**
     * 创建笔记任务
     *
     * @param noteTask 笔记任务
     * @return 创建后的笔记任务
     */
    NoteTask createNoteTask(NoteTask noteTask);
    
    /**
     * 获取笔记任务详情
     *
     * @param id 笔记任务ID
     * @return 笔记任务
     */
    Optional<NoteTask> getNoteTaskById(Long id);
    
    /**
     * 获取用户的笔记任务列表
     *
     * @param userId 用户ID
     * @return 笔记任务列表
     */
    List<NoteTask> getNoteTasksByUserId(Long userId);
    
    /**
     * 获取项目的笔记任务列表
     *
     * @param projectId 项目ID
     * @return 笔记任务列表
     */
    List<NoteTask> getNoteTasksByProjectId(Long projectId);
    
    /**
     * 获取思维导图的笔记任务列表
     *
     * @param mindMapId 思维导图ID
     * @return 笔记任务列表
     */
    List<NoteTask> getNoteTasksByMindMapId(Long mindMapId);
    
    /**
     * 获取文件的笔记任务列表
     *
     * @param fileId 文件ID
     * @return 笔记任务列表
     */
    List<NoteTask> getNoteTasksByFileId(Long fileId);
    
    /**
     * 更新笔记任务
     *
     * @param noteTask 笔记任务
     * @return 更新后的笔记任务
     */
    NoteTask updateNoteTask(NoteTask noteTask);
    
    /**
     * 更新笔记任务状态
     *
     * @param id 笔记任务ID
     * @param status 任务状态
     * @return 更新后的笔记任务
     */
    NoteTask updateNoteTaskStatus(Long id, String status);
    
    /**
     * 更新笔记任务结果
     *
     * @param id 笔记任务ID
     * @param result 任务结果
     * @return 更新后的笔记任务
     */
    NoteTask updateNoteTaskResult(Long id, String result);
    
    /**
     * 删除笔记任务
     *
     * @param id 笔记任务ID
     */
    void deleteNoteTask(Long id);
} 