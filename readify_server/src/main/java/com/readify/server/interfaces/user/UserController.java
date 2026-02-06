package com.readify.server.interfaces.user;

import com.readify.server.domain.user.model.User;
import com.readify.server.domain.user.service.UserService;
import com.readify.server.infrastructure.common.Result;
import com.readify.server.interfaces.user.converter.UserVOConverter;
import com.readify.server.interfaces.user.vo.UserVO;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.Parameter;
import io.swagger.v3.oas.annotations.tags.Tag;
import lombok.RequiredArgsConstructor;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.web.bind.annotation.DeleteMapping;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PutMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.List;

@RestController
@RequestMapping("/users")
@RequiredArgsConstructor
@Tag(name = "用户管理", description = "用户信息管理")
public class UserController {
    private final UserService userService;

    @Operation(summary = "更新用户")
    @PutMapping("/{id}")
    @PreAuthorize("hasAuthority('USER:WRITE')")
    public Result<UserVO> updateUser(
            @Parameter(description = "用户ID") @PathVariable Long id,
            @RequestBody UserVO userVO) {
        User user = UserVOConverter.INSTANCE.toDomain(userVO);
        user.setId(id);
        User updatedUser = userService.updateUser(user);
        return Result.success(UserVOConverter.INSTANCE.toVO(updatedUser));
    }

    @Operation(summary = "删除用户")
    @DeleteMapping("/{id}")
    @PreAuthorize("hasAuthority('USER:WRITE')")
    public Result<Void> deleteUser(@Parameter(description = "用户ID") @PathVariable Long id) {
        userService.deleteUser(id);
        return Result.success();
    }

    @Operation(summary = "按ID查询用户")
    @GetMapping("/{id}")
    @PreAuthorize("hasAuthority('USER:READ')")
    public Result<UserVO> getUserById(@Parameter(description = "用户ID") @PathVariable Long id) {
        User user = userService.getUserById(id);
        return Result.success(UserVOConverter.INSTANCE.toVO(user));
    }

    @Operation(summary = "按用户名查询用户")
    @GetMapping("/username/{username}")
    @PreAuthorize("hasAuthority('USER:READ')")
    public Result<UserVO> getUserByUsername(@Parameter(description = "用户名") @PathVariable String username) {
        User user = userService.getUserByUsername(username);
        return Result.success(UserVOConverter.INSTANCE.toVO(user));
    }

    @Operation(summary = "查询所有用户")
    @GetMapping
    @PreAuthorize("hasAuthority('USER:READ')")
    public Result<List<UserVO>> getAllUsers() {
        List<User> users = userService.getAllUsers();
        return Result.success(UserVOConverter.INSTANCE.toVOList(users));
    }

    @Operation(summary = "检查用户名是否存在")
    @GetMapping("/check/{username}")
    @PreAuthorize("hasAuthority('USER:READ')")
    public Result<Boolean> checkUsername(@Parameter(description = "用户名") @PathVariable String username) {
        return Result.success(userService.isUsernameExists(username));
    }
}

