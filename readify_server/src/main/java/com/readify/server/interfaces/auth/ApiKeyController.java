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
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.web.bind.annotation.DeleteMapping;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.List;
import java.util.stream.Collectors;

@Slf4j
@RestController
@RequestMapping("/auth/api-keys")
@RequiredArgsConstructor
@Tag(name = "API Key管理", description = "API Key 创建、查询、删除")
public class ApiKeyController {
    private final ApiKeyService apiKeyService;

    @PostMapping
    @Operation(summary = "创建API Key")
    @PreAuthorize("hasAuthority('API_KEY:MANAGE')")
    public Result<ApiKeyVO> create(@RequestBody CreateApiKeyReq req) {
        ApiKey apiKey = apiKeyService.create(req.getName(), req.getDescription());
        return Result.success(ApiKeyVO.from(apiKey));
    }

    @GetMapping
    @Operation(summary = "查询API Key列表")
    @PreAuthorize("hasAuthority('API_KEY:MANAGE')")
    public Result<List<ApiKeyVO>> list() {
        List<ApiKey> apiKeys = apiKeyService.list();
        return Result.success(apiKeys.stream().map(ApiKeyVO::from).collect(Collectors.toList()));
    }

    @DeleteMapping("/{id}")
    @Operation(summary = "删除API Key")
    @PreAuthorize("hasAuthority('API_KEY:MANAGE')")
    public Result<Void> delete(@Parameter(description = "API Key ID") @PathVariable Long id) {
        apiKeyService.delete(id);
        return Result.success();
    }
}
