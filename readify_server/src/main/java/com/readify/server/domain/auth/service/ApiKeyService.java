package com.readify.server.domain.auth.service;

import com.readify.server.domain.auth.model.ApiKey;

import java.util.List;

public interface ApiKeyService {
    /**
     * 创建API Key
     *
     * @param name API Key名称
     * @param description API Key描述
     * @return API Key信息
     */
    ApiKey create(String name, String description);

    /**
     * 获取API Key列表
     *
     * @return API Key列表
     */
    List<ApiKey> list();

    /**
     * 删除API Key
     *
     * @param id API Key ID
     */
    void delete(Long id);

    /**
     * 验证API Key
     *
     * @param key API Key
     * @return API Key信息，如果验证失败返回null
     */
    ApiKey validate(String key);
} 