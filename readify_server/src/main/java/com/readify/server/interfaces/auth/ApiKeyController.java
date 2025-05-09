package com.readify.server.interfaces.auth;

import com.readify.server.domain.auth.model.ApiKey;
import com.readify.server.domain.auth.service.ApiKeyService;
import com.readify.server.infrastructure.common.Result;
import com.readify.server.interfaces.auth.req.CreateApiKeyReq;
import com.readify.server.interfaces.auth.vo.ApiKeyVO;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.Parameter;
import io.swagger.v3.oas.annotations.tags.Tag;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.web.bind.annotation.*;

import java.util.List;
import java.util.stream.Collectors;

@Slf4j
@RestController
@RequestMapping("/api/v1/auth/api-keys")
@RequiredArgsConstructor
@Tag(name = "API Key管理", description = "API Key管理相关接口")
public class ApiKeyController {
    private final ApiKeyService apiKeyService;

    @PostMapping
    @Operation(summary = "创建API Key")
    public Result<ApiKeyVO> create(@RequestBody CreateApiKeyReq req) {
        ApiKey apiKey = apiKeyService.create(req.getName(), req.getDescription());
        return Result.success(ApiKeyVO.from(apiKey));
    }

    @GetMapping
    @Operation(summary = "获取API Key列表")
    public Result<List<ApiKeyVO>> list() {
        List<ApiKey> apiKeys = apiKeyService.list();
        return Result.success(apiKeys.stream().map(ApiKeyVO::from).collect(Collectors.toList()));
    }

    @DeleteMapping("/{id}")
    @Operation(summary = "删除API Key")
    public Result<Void> delete(@Parameter(description = "API Key ID") @PathVariable Long id) {
        apiKeyService.delete(id);
        return Result.success();
    }
} 