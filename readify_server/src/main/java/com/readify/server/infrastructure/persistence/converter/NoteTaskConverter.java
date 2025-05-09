package com.readify.server.infrastructure.persistence.converter;

import com.readify.server.domain.notetask.model.NoteTask;
import com.readify.server.infrastructure.persistence.entity.NoteTaskEntity;
import org.springframework.stereotype.Component;

import java.util.List;
import java.util.stream.Collectors;

/**
 * 笔记任务领域模型与持久化实体转换器
 */
@Component
public class NoteTaskConverter {

    /**
     * 持久化实体转领域模型
     *
     * @param entity 持久化实体
     * @return 领域模型
     */
    public NoteTask toDomain(NoteTaskEntity entity) {
        if (entity == null) {
            return null;
        }
        
        return NoteTask.builder()
                .id(entity.getId())
                .userId(entity.getUserId())
                .projectId(entity.getProjectId())
                .mindMapId(entity.getMindMapId())
                .fileId(entity.getFileId())
                .content(entity.getContent())
                .status(entity.getStatus())
                .result(entity.getResult())
                .createTime(entity.getCreateTime())
                .updateTime(entity.getUpdateTime())
                .deleted(entity.getDeleted())
                .build();
    }

    /**
     * 领域模型转持久化实体
     *
     * @param domain 领域模型
     * @return 持久化实体
     */
    public NoteTaskEntity toEntity(NoteTask domain) {
        if (domain == null) {
            return null;
        }
        
        return NoteTaskEntity.builder()
                .id(domain.getId())
                .userId(domain.getUserId())
                .projectId(domain.getProjectId())
                .mindMapId(domain.getMindMapId())
                .fileId(domain.getFileId())
                .content(domain.getContent())
                .status(domain.getStatus())
                .result(domain.getResult())
                .createTime(domain.getCreateTime())
                .updateTime(domain.getUpdateTime())
                .deleted(domain.getDeleted())
                .build();
    }

    /**
     * 持久化实体列表转领域模型列表
     *
     * @param entities 持久化实体列表
     * @return 领域模型列表
     */
    public List<NoteTask> toDomainList(List<NoteTaskEntity> entities) {
        if (entities == null) {
            return null;
        }
        
        return entities.stream()
                .map(this::toDomain)
                .collect(Collectors.toList());
    }

    /**
     * 领域模型列表转持久化实体列表
     *
     * @param domains 领域模型列表
     * @return 持久化实体列表
     */
    public List<NoteTaskEntity> toEntityList(List<NoteTask> domains) {
        if (domains == null) {
            return null;
        }
        
        return domains.stream()
                .map(this::toEntity)
                .collect(Collectors.toList());
    }
}