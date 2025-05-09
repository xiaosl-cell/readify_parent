package com.readify.server.interfaces.auth.vo;

import com.readify.server.domain.auth.model.ApiKey;
import io.swagger.v3.oas.annotations.media.Schema;
import lombok.Data;

@Data
@Schema(description = "API Key信息")
public class ApiKeyVO {
    @Schema(description = "API Key ID")
    private Long id;

    @Schema(description = "API Key名称")
    private String name;

    @Schema(description = "API Key")
    private String apiKey;

    @Schema(description = "API Key描述")
    private String description;

    @Schema(description = "是否启用")
    private Boolean enabled;

    @Schema(description = "创建时间")
    private Long createTime;

    public static ApiKeyVO from(ApiKey apiKey) {
        if (apiKey == null) {
            return null;
        }
        ApiKeyVO vo = new ApiKeyVO();
        vo.setId(apiKey.getId());
        vo.setName(apiKey.getName());
        vo.setApiKey(apiKey.getApiKey());
        vo.setDescription(apiKey.getDescription());
        vo.setEnabled(apiKey.getEnabled());
        vo.setCreateTime(apiKey.getCreateTime());
        return vo;
    }
} 