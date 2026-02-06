package com.readify.server.infrastructure.persistence.entity;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableLogic;
import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Data;

@Data
@TableName("sys_permission")
public class PermissionEntity {
    @TableId(type = IdType.AUTO)
    private Long id;

    private String code;

    private String name;

    private String module;

    private String description;

    private Boolean enabled;

    private Long createTime;

    private Long updateTime;

    @TableLogic
    private Boolean deleted;
}
