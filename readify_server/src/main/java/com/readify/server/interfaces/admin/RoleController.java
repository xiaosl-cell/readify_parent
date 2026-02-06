package com.readify.server.interfaces.admin;

import com.readify.server.domain.auth.model.Role;
import com.readify.server.domain.auth.model.Permission;
import com.readify.server.domain.auth.service.RbacManageService;
import com.readify.server.infrastructure.common.PageResult;
import com.readify.server.infrastructure.common.Result;
import com.readify.server.interfaces.admin.converter.AdminConverter;
import com.readify.server.interfaces.admin.req.AssignPermissionsReq;
import com.readify.server.interfaces.admin.req.RoleCreateReq;
import com.readify.server.interfaces.admin.req.RoleUpdateReq;
import com.readify.server.interfaces.admin.vo.PermissionVO;
import com.readify.server.interfaces.admin.vo.RoleVO;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.Parameter;
import io.swagger.v3.oas.annotations.tags.Tag;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.web.bind.annotation.*;

import java.util.List;
import java.util.stream.Collectors;

@RestController
@RequestMapping("/admin/roles")
@RequiredArgsConstructor
@Tag(name = "角色管理", description = "角色CRUD及权限分配")
@PreAuthorize("hasRole('ADMIN')")
public class RoleController {
    private final RbacManageService rbacManageService;

    @Operation(summary = "创建角色")
    @PostMapping
    public Result<RoleVO> createRole(@Valid @RequestBody RoleCreateReq req) {
        Role role = AdminConverter.toRole(req);
        Role created = rbacManageService.createRole(role);
        return Result.success(AdminConverter.toRoleVO(created));
    }

    @Operation(summary = "更新角色")
    @PutMapping("/{id}")
    public Result<RoleVO> updateRole(
            @Parameter(description = "角色ID") @PathVariable Long id,
            @Valid @RequestBody RoleUpdateReq req) {
        Role role = AdminConverter.toRole(req);
        role.setId(id);
        Role updated = rbacManageService.updateRole(role);
        return Result.success(AdminConverter.toRoleVO(updated));
    }

    @Operation(summary = "删除角色")
    @DeleteMapping("/{id}")
    public Result<Void> deleteRole(@Parameter(description = "角色ID") @PathVariable Long id) {
        rbacManageService.deleteRole(id);
        return Result.success();
    }

    @Operation(summary = "获取角色详情")
    @GetMapping("/{id}")
    public Result<RoleVO> getRoleById(@Parameter(description = "角色ID") @PathVariable Long id) {
        Role role = rbacManageService.getRoleById(id);
        return Result.success(AdminConverter.toRoleVO(role));
    }

    @Operation(summary = "分页查询角色")
    @GetMapping
    public Result<PageResult<RoleVO>> getRolesPage(
            @Parameter(description = "页码") @RequestParam(defaultValue = "1") int page,
            @Parameter(description = "每页数量") @RequestParam(defaultValue = "10") int size,
            @Parameter(description = "搜索关键字") @RequestParam(required = false) String keyword) {
        PageResult<Role> pageResult = rbacManageService.getRolesPage(page, size, keyword);
        List<RoleVO> voList = pageResult.getItems().stream()
                .map(AdminConverter::toRoleVO)
                .collect(Collectors.toList());
        return Result.success(PageResult.of(voList, pageResult.getTotal(), page, size));
    }

    @Operation(summary = "获取所有角色")
    @GetMapping("/all")
    public Result<List<RoleVO>> getAllRoles() {
        List<Role> roles = rbacManageService.getAllRoles();
        List<RoleVO> voList = roles.stream()
                .map(AdminConverter::toRoleVO)
                .collect(Collectors.toList());
        return Result.success(voList);
    }

    @Operation(summary = "分配权限给角色")
    @PostMapping("/{id}/permissions")
    public Result<Void> assignPermissions(
            @Parameter(description = "角色ID") @PathVariable Long id,
            @Valid @RequestBody AssignPermissionsReq req) {
        rbacManageService.assignPermissionsToRole(id, req.getPermissionIds());
        return Result.success();
    }

    @Operation(summary = "获取角色的权限列表")
    @GetMapping("/{id}/permissions")
    public Result<List<PermissionVO>> getRolePermissions(
            @Parameter(description = "角色ID") @PathVariable Long id) {
        List<Permission> permissions = rbacManageService.getPermissionsByRoleId(id);
        List<PermissionVO> voList = permissions.stream()
                .map(AdminConverter::toPermissionVO)
                .collect(Collectors.toList());
        return Result.success(voList);
    }
}
