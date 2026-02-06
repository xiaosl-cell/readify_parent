package com.readify.server.infrastructure.persistence.repository;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.readify.server.domain.auth.model.ApiKey;
import com.readify.server.domain.auth.repository.ApiKeyRepository;
import com.readify.server.infrastructure.persistence.entity.ApiKeyEntity;
import com.readify.server.infrastructure.persistence.mapper.ApiKeyMapper;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Repository;

import java.util.List;
import java.util.Optional;
import java.util.stream.Collectors;

@Repository
@RequiredArgsConstructor
public class ApiKeyRepositoryImpl implements ApiKeyRepository {
    private final ApiKeyMapper apiKeyMapper;

    @Override
    public ApiKey save(ApiKey apiKey) {
        ApiKeyEntity entity = toEntity(apiKey);
        if (apiKey.getId() == null) {
            apiKeyMapper.insert(entity);
        } else {
            apiKeyMapper.updateById(entity);
        }
        return toApiKey(entity);
    }

    @Override
    public ApiKey findByKey(String key) {
        LambdaQueryWrapper<ApiKeyEntity> queryWrapper = new LambdaQueryWrapper<>();
        queryWrapper.eq(ApiKeyEntity::getApiKey, key);
        ApiKeyEntity entity = apiKeyMapper.selectOne(queryWrapper);
        return toApiKey(entity);
    }

    @Override
    public Optional<ApiKey> findById(Long id) {
        return Optional.ofNullable(apiKeyMapper.selectById(id)).map(this::toApiKey);
    }

    @Override
    public List<ApiKey> findByUserId(Long userId) {
        LambdaQueryWrapper<ApiKeyEntity> queryWrapper = new LambdaQueryWrapper<>();
        queryWrapper.eq(ApiKeyEntity::getUserId, userId);
        return apiKeyMapper.selectList(queryWrapper)
                .stream()
                .map(this::toApiKey)
                .collect(Collectors.toList());
    }

    @Override
    public void delete(Long id) {
        apiKeyMapper.deleteById(id);
    }

    private ApiKeyEntity toEntity(ApiKey apiKey) {
        if (apiKey == null) {
            return null;
        }
        ApiKeyEntity entity = new ApiKeyEntity();
        entity.setId(apiKey.getId());
        entity.setName(apiKey.getName());
        entity.setApiKey(apiKey.getApiKey());
        entity.setDescription(apiKey.getDescription());
        entity.setUserId(apiKey.getUserId());
        entity.setEnabled(apiKey.getEnabled());
        entity.setCreateTime(apiKey.getCreateTime());
        entity.setUpdateTime(apiKey.getUpdateTime());
        return entity;
    }

    private ApiKey toApiKey(ApiKeyEntity entity) {
        if (entity == null) {
            return null;
        }
        ApiKey apiKey = new ApiKey();
        apiKey.setId(entity.getId());
        apiKey.setName(entity.getName());
        apiKey.setApiKey(entity.getApiKey());
        apiKey.setDescription(entity.getDescription());
        apiKey.setUserId(entity.getUserId());
        apiKey.setEnabled(entity.getEnabled());
        apiKey.setCreateTime(entity.getCreateTime());
        apiKey.setUpdateTime(entity.getUpdateTime());
        return apiKey;
    }
} 
