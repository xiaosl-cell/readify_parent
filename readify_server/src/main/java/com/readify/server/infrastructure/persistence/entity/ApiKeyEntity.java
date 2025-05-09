package com.readify.server.infrastructure.persistence.entity;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableField;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Data;

@Data
@TableName("api_keys")
public class ApiKeyEntity {
    @TableId(type = IdType.AUTO)
    private Long id;
    private String name;
    @TableField("api_key")
    private String apiKey;
    private String description;
    private Long userId;
    private Boolean enabled;
    private Long createTime;
    private Long updateTime;
} 