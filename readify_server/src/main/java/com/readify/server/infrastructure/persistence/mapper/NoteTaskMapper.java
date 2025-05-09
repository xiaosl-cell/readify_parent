package com.readify.server.infrastructure.persistence.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.readify.server.infrastructure.persistence.entity.NoteTaskEntity;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;
import org.apache.ibatis.annotations.Select;

import java.util.List;

/**
 * 笔记任务Mapper接口
 */
@Mapper
public interface NoteTaskMapper extends BaseMapper<NoteTaskEntity> {
    
    /**
     * 根据用户ID查询笔记任务列表
     *
     * @param userId 用户ID
     * @return 笔记任务列表
     */
    @Select("SELECT * FROM note_task WHERE user_id = #{userId} AND deleted = 0")
    List<NoteTaskEntity> findByUserId(@Param("userId") Long userId);
    
    /**
     * 根据项目ID查询笔记任务列表
     *
     * @param projectId 项目ID
     * @return 笔记任务列表
     */
    @Select("SELECT * FROM note_task WHERE project_id = #{projectId} AND deleted = 0")
    List<NoteTaskEntity> findByProjectId(@Param("projectId") Long projectId);
    
    /**
     * 根据思维导图ID查询笔记任务列表
     *
     * @param mindMapId 思维导图ID
     * @return 笔记任务列表
     */
    @Select("SELECT * FROM note_task WHERE mind_map_id = #{mindMapId} AND deleted = 0")
    List<NoteTaskEntity> findByMindMapId(@Param("mindMapId") Long mindMapId);
    
    /**
     * 根据文件ID查询笔记任务列表
     *
     * @param fileId 文件ID
     * @return 笔记任务列表
     */
    @Select("SELECT * FROM note_task WHERE file_id = #{fileId} AND deleted = 0")
    List<NoteTaskEntity> findByFileId(@Param("fileId") Long fileId);
} 