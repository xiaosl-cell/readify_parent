package com.readify.server.domain.auth.service.impl;

import com.readify.server.domain.auth.model.ApiKey;
import com.readify.server.domain.auth.repository.ApiKeyRepository;
import com.readify.server.domain.auth.service.ApiKeyService;
import com.readify.server.infrastructure.common.exception.ForbiddenException;
import com.readify.server.infrastructure.common.exception.NotFoundException;
import com.readify.server.infrastructure.security.SecurityUtils;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.security.SecureRandom;
import java.util.Base64;
import java.util.List;

@Slf4j
@Service
@RequiredArgsConstructor
public class ApiKeyServiceImpl implements ApiKeyService {
    private final ApiKeyRepository apiKeyRepository;
    private static final SecureRandom secureRandom = new SecureRandom();

    @Override
    @Transactional
    public ApiKey create(String name, String description) {
        ApiKey apiKey = new ApiKey();
        apiKey.setName(name);
        apiKey.setDescription(description);
        apiKey.setApiKey(generateApiKey());
        apiKey.setUserId(SecurityUtils.getCurrentUserId());
        apiKey.setEnabled(true);
        apiKey.setCreateTime(System.currentTimeMillis());
        apiKey.setUpdateTime(System.currentTimeMillis());
        return apiKeyRepository.save(apiKey);
    }

    @Override
    public List<ApiKey> list() {
        return apiKeyRepository.findByUserId(SecurityUtils.getCurrentUserId());
    }

    @Override
    @Transactional
    public void delete(Long id) {
        ApiKey apiKey = apiKeyRepository.findById(id)
                .orElseThrow(() -> new NotFoundException("API Key不存在"));
        if (!apiKey.getUserId().equals(SecurityUtils.getCurrentUserId())) {
            throw new ForbiddenException("无权限删除该API Key");
        }
        apiKeyRepository.delete(id);
    }

    @Override
    public ApiKey validate(String key) {
        ApiKey apiKey = apiKeyRepository.findByKey(key);
        if (apiKey != null && apiKey.getEnabled()) {
            return apiKey;
        }
        return null;
    }

    private String generateApiKey() {
        byte[] randomBytes = new byte[32];
        secureRandom.nextBytes(randomBytes);
        return Base64.getUrlEncoder().withoutPadding().encodeToString(randomBytes);
    }
} 
