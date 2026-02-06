package com.readify.server.interfaces.admin;

import com.readify.server.domain.auth.model.Permission;
import com.readify.server.domain.auth.service.RbacManageService;
import com.readify.server.infrastructure.common.PageResult;
import com.readify.server.infrastructure.common.Result;
import com.readify.server.interfaces.admin.converter.AdminConverter;
import com.readify.server.interfaces.admin.req.PermissionCreateReq;
import com.readify.server.interfaces.admin.req.PermissionUpdateReq;
import com.readify.server.interfaces.admin.vo.PermissionTreeVO;
import com.readify.server.interfaces.admin.vo.PermissionVO;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.Parameter;
import io.swagger.v3.oas.annotations.tags.Tag;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.web.bind.annotation.*;

import java.util.List;
import java.util.Map;
import java.util.stream.Collectors;

@RestController
@RequestMapping("/admin/permissions")
@RequiredArgsConstructor
@Tag(name = "权限管理", description = "权限CRUD")
@PreAuthorize("hasRole('ADMIN')")
public class PermissionController {
    private final RbacManageService rbacManageService;

    @Operation(summary = "创建权限")
    @PostMapping
    public Result<PermissionVO> createPermission(@Valid @RequestBody PermissionCreateReq req) {
        Permission permission = AdminConverter.toPermission(req);
        Permission created = rbacManageService.createPermission(permission);
        return Result.success(AdminConverter.toPermissionVO(created));
    }

    @Operation(summary = "更新权限")
    @PutMapping("/{id}")
    public Result<PermissionVO> updatePermission(
            @Parameter(description = "权限ID") @PathVariable Long id,
            @Valid @RequestBody PermissionUpdateReq req) {
        Permission permission = AdminConverter.toPermission(req);
        permission.setId(id);
        Permission updated = rbacManageService.updatePermission(permission);
        return Result.success(AdminConverter.toPermissionVO(updated));
    }

    @Operation(summary = "删除权限")
    @DeleteMapping("/{id}")
    public Result<Void> deletePermission(@Parameter(description = "权限ID") @PathVariable Long id) {
        rbacManageService.deletePermission(id);
        return Result.success();
    }

    @Operation(summary = "获取权限详情")
    @GetMapping("/{id}")
    public Result<PermissionVO> getPermissionById(@Parameter(description = "权限ID") @PathVariable Long id) {
        Permission permission = rbacManageService.getPermissionById(id);
        return Result.success(AdminConverter.toPermissionVO(permission));
    }

    @Operation(summary = "分页查询权限")
    @GetMapping
    public Result<PageResult<PermissionVO>> getPermissionsPage(
            @Parameter(description = "页码") @RequestParam(defaultValue = "1") int page,
            @Parameter(description = "每页数量") @RequestParam(defaultValue = "10") int size,
            @Parameter(description = "搜索关键字") @RequestParam(required = false) String keyword) {
        PageResult<Permission> pageResult = rbacManageService.getPermissionsPage(page, size, keyword);
        List<PermissionVO> voList = pageResult.getItems().stream()
                .map(AdminConverter::toPermissionVO)
                .collect(Collectors.toList());
        return Result.success(PageResult.of(voList, pageResult.getTotal(), page, size));
    }

    @Operation(summary = "获取所有权限")
    @GetMapping("/all")
    public Result<List<PermissionVO>> getAllPermissions() {
        List<Permission> permissions = rbacManageService.getAllPermissions();
        List<PermissionVO> voList = permissions.stream()
                .map(AdminConverter::toPermissionVO)
                .collect(Collectors.toList());
        return Result.success(voList);
    }

    @Operation(summary = "获取权限树（按模块分组）")
    @GetMapping("/tree")
    public Result<PermissionTreeVO> getPermissionTree() {
        Map<String, List<Permission>> tree = rbacManageService.getPermissionTree();
        Map<String, List<PermissionVO>> voTree = tree.entrySet().stream()
                .collect(Collectors.toMap(
                        Map.Entry::getKey,
                        e -> e.getValue().stream()
                                .map(AdminConverter::toPermissionVO)
                                .collect(Collectors.toList())
                ));
        return Result.success(PermissionTreeVO.builder().tree(voTree).build());
    }
}
