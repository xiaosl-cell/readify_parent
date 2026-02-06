package com.readify.server.interfaces.admin;

import com.readify.server.domain.auth.model.Role;
import com.readify.server.domain.auth.service.RbacManageService;
import com.readify.server.domain.user.model.User;
import com.readify.server.domain.user.service.UserService;
import com.readify.server.infrastructure.common.Result;
import com.readify.server.interfaces.admin.converter.AdminConverter;
import com.readify.server.interfaces.admin.req.AssignRolesReq;
import com.readify.server.interfaces.admin.vo.DashboardStatsVO;
import com.readify.server.interfaces.admin.vo.RoleVO;
import com.readify.server.interfaces.admin.vo.UserWithRolesVO;
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
@RequestMapping("/admin/users")
@RequiredArgsConstructor
@Tag(name = "用户角色管理", description = "管理用户角色分配")
@PreAuthorize("hasRole('ADMIN')")
public class AdminUserController {
    private final RbacManageService rbacManageService;
    private final UserService userService;

    @Operation(summary = "获取用户列表（含角色）")
    @GetMapping
    public Result<List<UserWithRolesVO>> getUsersWithRoles() {
        List<User> users = userService.getAllUsers();
        List<UserWithRolesVO> voList = users.stream()
                .map(user -> {
                    List<Role> roles = rbacManageService.getRolesByUserId(user.getId());
                    List<RoleVO> roleVOs = roles.stream()
                            .map(AdminConverter::toRoleVO)
                            .collect(Collectors.toList());
                    return UserWithRolesVO.builder()
                            .id(user.getId())
                            .username(user.getUsername())
                            .enabled(user.getEnabled())
                            .createTime(user.getCreateTime())
                            .roles(roleVOs)
                            .build();
                })
                .collect(Collectors.toList());
        return Result.success(voList);
    }

    @Operation(summary = "获取用户的角色列表")
    @GetMapping("/{id}/roles")
    public Result<List<RoleVO>> getUserRoles(@Parameter(description = "用户ID") @PathVariable Long id) {
        List<Role> roles = rbacManageService.getRolesByUserId(id);
        List<RoleVO> voList = roles.stream()
                .map(AdminConverter::toRoleVO)
                .collect(Collectors.toList());
        return Result.success(voList);
    }

    @Operation(summary = "分配角色给用户")
    @PostMapping("/{id}/roles")
    public Result<Void> assignRoles(
            @Parameter(description = "用户ID") @PathVariable Long id,
            @Valid @RequestBody AssignRolesReq req) {
        rbacManageService.assignRolesToUser(id, req.getRoleIds());
        return Result.success();
    }

    @Operation(summary = "获取仪表盘统计数据")
    @GetMapping("/stats")
    public Result<DashboardStatsVO> getDashboardStats() {
        DashboardStatsVO stats = DashboardStatsVO.builder()
                .userCount(rbacManageService.countUsers())
                .roleCount(rbacManageService.countRoles())
                .permissionCount(rbacManageService.countPermissions())
                .build();
        return Result.success(stats);
    }
}
