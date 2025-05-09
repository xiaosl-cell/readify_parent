package com.readify.server.interfaces.user.vo;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.Data;

@Data
@Schema(description = "用户视图对象")
public class UserVO {
    @Schema(description = "用户ID", accessMode = Schema.AccessMode.READ_ONLY)
    private Long id;

    @Schema(description = "用户名", example = "johndoe")
    private String username;

    @Schema(description = "账户是否启用", example = "true")
    private Boolean enabled;

    @Schema(description = "创建时间", accessMode = Schema.AccessMode.READ_ONLY)
    private Long createTime;

    @Schema(description = "更新时间", accessMode = Schema.AccessMode.READ_ONLY)
    private Long updateTime;
}