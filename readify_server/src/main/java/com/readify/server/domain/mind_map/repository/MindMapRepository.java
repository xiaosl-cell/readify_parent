package com.readify.server.domain.mind_map.repository;

import com.readify.server.domain.mind_map.model.MindMap;

import java.util.List;
import java.util.Optional;

public interface MindMapRepository {
    /**
     * 保存思维导图信息
     *
     * @param mindMap 思维导图信息
     * @return 保存后的思维导图信息
     */
    MindMap save(MindMap mindMap);

    /**
     * 根据ID查找思维导图
     *
     * @param id 思维导图ID
     * @return 思维导图信息
     */
    Optional<MindMap> findById(Long id);

    /**
     * 根据标题和用户ID查找思维导图
     *
     * @param title 思维导图标题
     * @param userId 用户ID
     * @return 思维导图信息
     */
    Optional<MindMap> findByTitleAndUserId(String title, Long userId);

    /**
     * 获取用户的所有思维导图
     *
     * @param userId 用户ID
     * @return 思维导图列表
     */
    List<MindMap> findByUserId(Long userId);

    /**
     * 获取项目下的所有思维导图
     *
     * @param projectId 项目ID
     * @return 思维导图列表
     */
    List<MindMap> findByProjectId(Long projectId);
    
    /**
     * 根据ID和用户ID删除思维导图（逻辑删除）
     *
     * @param id 思维导图ID
     * @param userId 用户ID
     * @return 受影响的行数
     */
    int deleteByIdAndUserId(Long id, Long userId);
    
    /**
     * 检查思维导图标题是否已存在
     *
     * @param title 思维导图标题
     * @param projectId 项目ID
     * @param userId 用户ID
     * @return true 如果标题已存在，否则返回 false
     */
    boolean existsByTitleAndProjectIdAndUserId(String title, Long projectId, Long userId);
} 