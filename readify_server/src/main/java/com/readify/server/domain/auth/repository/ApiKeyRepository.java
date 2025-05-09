package com.readify.server.domain.auth.repository;

import com.readify.server.domain.auth.model.ApiKey;

import java.util.List;

public interface ApiKeyRepository {
    /**
     * 保存API Key
     *
     * @param apiKey API Key信息
     * @return 保存后的API Key信息
     */
    ApiKey save(ApiKey apiKey);

    /**
     * 根据key查找API Key信息
     *
     * @param key API Key
     * @return API Key信息
     */
    ApiKey findByKey(String key);

    /**
     * 根据用户ID查找API Key列表
     *
     * @param userId 用户ID
     * @return API Key列表
     */
    List<ApiKey> findByUserId(Long userId);

    /**
     * 删除API Key
     *
     * @param id API Key ID
     */
    void delete(Long id);
} 