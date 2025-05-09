package com.readify.server.interfaces.auth.vo;

import com.readify.server.interfaces.user.vo.UserVO;
import io.swagger.v3.oas.annotations.media.Schema;
import lombok.Data;
import lombok.EqualsAndHashCode;

@Data
@Schema(description = "登录响应")
@EqualsAndHashCode(callSuper = true)
public class LoginVO extends UserVO {

    @Schema(description = "访问令牌", example = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...", accessMode = Schema.AccessMode.READ_ONLY)
    private String token;
}
