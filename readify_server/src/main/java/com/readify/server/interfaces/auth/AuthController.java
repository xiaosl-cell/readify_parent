package com.readify.server.interfaces.auth;

import com.readify.server.domain.auth.service.AuthService;
import com.readify.server.domain.auth.model.LoginResult;
import com.readify.server.infrastructure.common.Result;
import com.readify.server.interfaces.auth.converter.AuthVOConverter;
import com.readify.server.interfaces.auth.req.LoginReq;
import com.readify.server.interfaces.auth.req.RegisterReq;
import com.readify.server.interfaces.auth.vo.LoginVO;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.media.Content;
import io.swagger.v3.oas.annotations.media.Schema;
import io.swagger.v3.oas.annotations.responses.ApiResponse;
import io.swagger.v3.oas.annotations.responses.ApiResponses;
import io.swagger.v3.oas.annotations.tags.Tag;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.web.bind.annotation.*;

@Slf4j
@RestController
@RequestMapping("/auth")
@RequiredArgsConstructor
@Tag(name = "认证管理", description = "用户注册和登录相关接口")
public class AuthController {
    private final AuthService authService;
    private final AuthVOConverter authVOConverter = AuthVOConverter.INSTANCE;

    @PostMapping("/register")
    @Operation(summary = "用户注册", description = "创建新用户账号")
    @ApiResponses(value = {
            @ApiResponse(responseCode = "200", description = "注册成功"),
            @ApiResponse(responseCode = "400", description = "用户名已存在"),
            @ApiResponse(responseCode = "500", description = "系统异常")
    })
    public Result<Void> register(@RequestBody RegisterReq request) {
        log.info("收到注册请求: {}", request.getUsername());
        try {
            authService.register(
                    request.getUsername(),
                    request.getPassword()
            );
            return Result.success("注册成功");
        } catch (IllegalArgumentException e) {
            log.warn("注册失败: {}", e.getMessage());
            return Result.error(e.getMessage());
        } catch (Exception e) {
            log.error("注册异常", e);
            return Result.error("系统异常，请稍后重试");
        }
    }

    @PostMapping("/login")
    @Operation(summary = "用户登录", description = "验证用户凭证并返回访问令牌")
    @ApiResponses(value = {
            @ApiResponse(responseCode = "200", description = "登录成功",
                    content = @Content(schema = @Schema(implementation = LoginVO.class))),
    })
    public Result<LoginVO> login(@RequestBody LoginReq request) {
        log.info("收到登录请求: {}", request.getUsername());
        LoginResult result = authService.login(request.getUsername(), request.getPassword());
        LoginVO loginVO = new LoginVO();
        loginVO.setToken(result.getToken());
        // 复制用户信息
        authVOConverter.updateLoginVO(result.getUser(), loginVO);
        return Result.success(loginVO);

    }
}