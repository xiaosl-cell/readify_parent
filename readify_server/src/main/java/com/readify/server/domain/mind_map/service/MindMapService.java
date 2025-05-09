package com.readify.server.domain.mind_map.service;

import com.readify.server.domain.mind_map.model.MindMap;

import java.util.List;

public interface MindMapService {
    /**
     * 创建思维导图
     *
     * @param mindMap 思维导图信息
     * @param userId 用户ID
     * @return 创建后的思维导图
     */
    MindMap createMindMap(MindMap mindMap, Long userId);

    /**
     * 更新思维导图
     *
     * @param mindMap 思维导图信息
     * @param userId 用户ID
     * @return 更新后的思维导图
     */
    MindMap updateMindMap(MindMap mindMap, Long userId);

    /**
     * 获取思维导图
     *
     * @param id 思维导图ID
     * @param userId 用户ID
     * @return 思维导图信息
     */
    MindMap getMindMapById(Long id, Long userId);

    /**
     * 获取用户的所有思维导图
     *
     * @param userId 用户ID
     * @return 思维导图列表
     */
    List<MindMap> getUserMindMaps(Long userId);

    /**
     * 获取项目下的所有思维导图
     *
     * @param projectId 项目ID
     * @param userId 用户ID
     * @return 思维导图列表
     */
    List<MindMap> getProjectMindMaps(Long projectId, Long userId);

    /**
     * 删除思维导图
     *
     * @param id 思维导图ID
     * @param userId 用户ID
     * @return 是否删除成功
     */
    boolean deleteMindMap(Long id, Long userId);

    /**
     * 根据标题和用户ID获取思维导图
     *
     * @param title 思维导图标题
     * @param userId 用户ID
     * @return 思维导图信息
     */
    MindMap getMindMapByTitle(String title, Long userId);

    /**
     * 检查思维导图标题是否已存在于指定项目中
     *
     * @param title 思维导图标题
     * @param projectId 项目ID
     * @param userId 用户ID
     * @return true 如果标题已存在，否则返回 false
     */
    boolean isMindMapTitleExists(String title, Long projectId, Long userId);
} 