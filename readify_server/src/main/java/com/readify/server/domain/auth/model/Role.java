package com.readify.server.domain.auth.model;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class Role {
    private Long id;
    private String code;
    private String name;
    private String description;
    private Boolean enabled;
    private Long createTime;
    private Long updateTime;
}
