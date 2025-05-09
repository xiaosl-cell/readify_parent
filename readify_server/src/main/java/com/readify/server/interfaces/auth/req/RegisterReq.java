package com.readify.server.interfaces.auth.req;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.Data;

@Data
@Schema(description = "注册请求")
public class RegisterReq {

    @Schema(description = "用户名", example = "john.doe")
    private String username;

    @Schema(description = "密码")
    private String password;
}
