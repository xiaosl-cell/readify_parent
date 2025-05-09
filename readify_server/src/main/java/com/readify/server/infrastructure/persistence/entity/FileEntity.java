package com.readify.server.infrastructure.persistence.entity;

import com.baomidou.mybatisplus.annotation.*;
import io.swagger.v3.oas.annotations.media.Schema;
import lombok.Data;

@Data
@TableName("file")
@Schema(description = "文件实体")
public class FileEntity {
    
    @TableId(type = IdType.AUTO)
    @Schema(description = "主键ID")
    private Long id;

    @Schema(description = "原始文件名")
    private String originalName;

    @Schema(description = "存储文件名")
    private String storageName;

    @Schema(description = "文件大小(字节)")
    private Long size;

    @Schema(description = "文件MIME类型")
    private String mimeType;

    @Schema(description = "存储路径")
    private String storagePath;

    @Schema(description = "文件MD5值")
    private String md5;

    @Schema(description = "创建时间")
    private Long createTime;

    @Schema(description = "更新时间")
    private Long updateTime;

    @TableLogic
    @Schema(description = "是否删除")
    private Boolean deleted;

    @Schema(description = "是否已向量化")
    private Boolean vectorized;
} 