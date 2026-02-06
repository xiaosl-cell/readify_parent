package com.readify.server.interfaces.auth;

import com.readify.server.domain.auth.model.LoginResult;
import com.readify.server.domain.auth.service.AuthService;
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
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@Slf4j
@RestController
@RequestMapping("/auth")
@RequiredArgsConstructor
@Tag(name = "认证管理", description = "用户注册与登录")
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
        log.info("Register request: {}", request.getUsername());
        authService.register(request.getUsername(), request.getPassword());
        return Result.success("注册成功");
    }

    @PostMapping("/login")
    @Operation(summary = "用户登录", description = "验证用户凭证并返回访问令牌")
    @ApiResponses(value = {
            @ApiResponse(responseCode = "200", description = "登录成功",
                    content = @Content(schema = @Schema(implementation = LoginVO.class))),
    })
    public Result<LoginVO> login(@RequestBody LoginReq request) {
        log.info("Login request: {}", request.getUsername());
        LoginResult result = authService.login(request.getUsername(), request.getPassword());
        LoginVO loginVO = new LoginVO();
        loginVO.setToken(result.getToken());
        authVOConverter.updateLoginVO(result.getUser(), loginVO);
        return Result.success(loginVO);
    }
}

