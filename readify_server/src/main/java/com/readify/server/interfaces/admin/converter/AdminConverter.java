package com.readify.server.interfaces.admin.converter;

import com.readify.server.domain.auth.model.Permission;
import com.readify.server.domain.auth.model.Role;
import com.readify.server.interfaces.admin.req.PermissionCreateReq;
import com.readify.server.interfaces.admin.req.PermissionUpdateReq;
import com.readify.server.interfaces.admin.req.RoleCreateReq;
import com.readify.server.interfaces.admin.req.RoleUpdateReq;
import com.readify.server.interfaces.admin.vo.PermissionVO;
import com.readify.server.interfaces.admin.vo.RoleVO;

public class AdminConverter {

    public static Role toRole(RoleCreateReq req) {
        return Role.builder()
                .code(req.getCode())
                .name(req.getName())
                .description(req.getDescription())
                .enabled(req.getEnabled())
                .build();
    }

    public static Role toRole(RoleUpdateReq req) {
        return Role.builder()
                .code(req.getCode())
                .name(req.getName())
                .description(req.getDescription())
                .enabled(req.getEnabled())
                .build();
    }

    public static RoleVO toRoleVO(Role role) {
        return RoleVO.builder()
                .id(role.getId())
                .code(role.getCode())
                .name(role.getName())
                .description(role.getDescription())
                .enabled(role.getEnabled())
                .createTime(role.getCreateTime())
                .updateTime(role.getUpdateTime())
                .build();
    }

    public static Permission toPermission(PermissionCreateReq req) {
        return Permission.builder()
                .code(req.getCode())
                .name(req.getName())
                .module(req.getModule())
                .description(req.getDescription())
                .enabled(req.getEnabled())
                .build();
    }

    public static Permission toPermission(PermissionUpdateReq req) {
        return Permission.builder()
                .code(req.getCode())
                .name(req.getName())
                .module(req.getModule())
                .description(req.getDescription())
                .enabled(req.getEnabled())
                .build();
    }

    public static PermissionVO toPermissionVO(Permission permission) {
        return PermissionVO.builder()
                .id(permission.getId())
                .code(permission.getCode())
                .name(permission.getName())
                .module(permission.getModule())
                .description(permission.getDescription())
                .enabled(permission.getEnabled())
                .createTime(permission.getCreateTime())
                .updateTime(permission.getUpdateTime())
                .build();
    }
}
