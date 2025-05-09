package com.readify.server.domain.mind_map.service.impl;

import com.readify.server.domain.mind_map.model.MindMap;
import com.readify.server.domain.mind_map.model.MindMapNode;
import com.readify.server.domain.mind_map.repository.MindMapRepository;
import com.readify.server.domain.mind_map.service.MindMapNodeService;
import com.readify.server.domain.mind_map.service.MindMapService;
import com.readify.server.infrastructure.common.exception.BusinessException;
import com.readify.server.infrastructure.common.exception.ForbiddenException;
import com.readify.server.infrastructure.common.exception.NotFoundException;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;
import java.util.Optional;
import java.util.stream.Collectors;

@Service
@RequiredArgsConstructor
public class MindMapServiceImpl implements MindMapService {
    private final MindMapRepository mindMapRepository;
    private final MindMapNodeService mindMapNodeService;

    @Override
    @Transactional(rollbackFor = Exception.class)
    public MindMap createMindMap(MindMap mindMap, Long userId) {
        // 检查同一项目中是否已存在相同标题的思维导图
        if (mindMapRepository.existsByTitleAndProjectIdAndUserId(mindMap.getTitle(), mindMap.getProjectId(), userId)) {
            throw new BusinessException("该项目中已存在相同标题的思维导图");
        }
        
        // 设置思维导图基本信息
        mindMap.setUserId(userId);
        mindMap.setCreatedAt(System.currentTimeMillis());
        mindMap.setUpdatedAt(System.currentTimeMillis());
        mindMap.setIsDeleted(false);
        
        // 保存思维导图
        MindMap savedMindMap = mindMapRepository.save(mindMap);
        
        // 创建根节点
        createRootNode(savedMindMap);
        
        return savedMindMap;
    }

    /**
     * 创建思维导图的根节点
     *
     * @param mindMap 思维导图信息
     */
    private void createRootNode(MindMap mindMap) {
        MindMapNode rootNode = new MindMapNode();
        rootNode.setProjectId(mindMap.getProjectId());
        rootNode.setMindMapId(mindMap.getId());
        rootNode.setFileId(mindMap.getFileId());
        rootNode.setMindMapId(mindMap.getId());
        rootNode.setParentId(null); // 根节点没有父节点
        rootNode.setContent(mindMap.getTitle()); // 根节点内容为思维导图标题
        rootNode.setSequence(0); // 根节点序号为0
        rootNode.setLevel(0); // 根节点层级为0
        rootNode.setCreatedTime(System.currentTimeMillis());
        rootNode.setUpdatedTime(System.currentTimeMillis());
        rootNode.setDeleted(false);
        
        // 保存根节点
        mindMapNodeService.saveNode(rootNode);
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public MindMap updateMindMap(MindMap mindMap, Long userId) {
        MindMap existingMindMap = getMindMapById(mindMap.getId(), userId);
        
        // 如果标题或项目ID发生变化，需要检查新标题在项目中是否已存在
        if ((!existingMindMap.getTitle().equals(mindMap.getTitle()) || 
             !existingMindMap.getProjectId().equals(mindMap.getProjectId())) &&
            mindMapRepository.existsByTitleAndProjectIdAndUserId(mindMap.getTitle(), mindMap.getProjectId(), userId)) {
            throw new BusinessException("该项目中已存在相同标题的思维导图");
        }
        
        // 设置保留原有的属性
        mindMap.setUserId(userId);
        mindMap.setCreatedAt(existingMindMap.getCreatedAt());
        mindMap.setUpdatedAt(System.currentTimeMillis());
        mindMap.setIsDeleted(existingMindMap.getIsDeleted());
        
        // 如果标题发生变化，需要更新根节点
        boolean titleChanged = !existingMindMap.getTitle().equals(mindMap.getTitle());
        
        // 保存思维导图
        MindMap updatedMindMap = mindMapRepository.save(mindMap);
        
        // 如果标题变化，更新根节点
        if (titleChanged) {
            updateRootNodeContent(updatedMindMap);
        }
        
        return updatedMindMap;
    }
    
    /**
     * 更新思维导图根节点的内容
     *
     * @param mindMap 思维导图信息
     */
    private void updateRootNodeContent(MindMap mindMap) {
        try {
            // 查找根节点
            Optional<MindMapNode> rootNodeOpt = mindMapNodeService.findRootNodeByMindMapId(mindMap.getId());
            
            if (rootNodeOpt.isPresent()) {
                MindMapNode rootNode = rootNodeOpt.get();
                rootNode.setContent(mindMap.getTitle()); // 更新根节点内容为新的思维导图标题
                rootNode.setUpdatedTime(System.currentTimeMillis());
                
                // 保存更新后的根节点
                mindMapNodeService.saveNode(rootNode);
            } else {
                // 如果不存在根节点，创建一个新的根节点
                createRootNode(mindMap);
            }
        } catch (Exception e) {
            // 记录错误，但不影响主流程
            // 如果有日志系统，这里应该记录日志
            System.err.println("更新思维导图根节点失败: " + e.getMessage());
        }
    }

    @Override
    public MindMap getMindMapById(Long id, Long userId) {
        MindMap mindMap = mindMapRepository.findById(id)
                .orElseThrow(() -> new NotFoundException("思维导图不存在"));
                
        if (!mindMap.getUserId().equals(userId)) {
            throw new ForbiddenException("无权访问此思维导图");
        }
        
        if (Boolean.TRUE.equals(mindMap.getIsDeleted())) {
            throw new NotFoundException("思维导图不存在或已被删除");
        }
        
        return mindMap;
    }

    @Override
    public List<MindMap> getUserMindMaps(Long userId) {
        return mindMapRepository.findByUserId(userId).stream()
                .filter(mindMap -> !Boolean.TRUE.equals(mindMap.getIsDeleted()))
                .collect(Collectors.toList());
    }

    @Override
    public List<MindMap> getProjectMindMaps(Long projectId, Long userId) {
        return mindMapRepository.findByProjectId(projectId).stream()
                .filter(mindMap -> mindMap.getUserId().equals(userId) && !Boolean.TRUE.equals(mindMap.getIsDeleted()))
                .collect(Collectors.toList());
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public boolean deleteMindMap(Long id, Long userId) {
        // 确保思维导图存在且属于该用户
        MindMap mindMap = getMindMapById(id, userId);
        
        // 删除思维导图的所有节点
        mindMapNodeService.deleteNodesByMindMapId(mindMap.getId());
        
        // 执行逻辑删除
        return mindMapRepository.deleteByIdAndUserId(id, userId) > 0;
    }

    @Override
    public MindMap getMindMapByTitle(String title, Long userId) {
        return mindMapRepository.findByTitleAndUserId(title, userId)
                .filter(mindMap -> !Boolean.TRUE.equals(mindMap.getIsDeleted()))
                .orElseThrow(() -> new NotFoundException("思维导图不存在"));
    }

    @Override
    public boolean isMindMapTitleExists(String title, Long projectId, Long userId) {
        return mindMapRepository.existsByTitleAndProjectIdAndUserId(title, projectId, userId);
    }
} 