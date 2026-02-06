package com.readify.server.infrastructure.persistence.entity;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableField;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableLogic;
import com.baomidou.mybatisplus.annotation.TableName;
import io.swagger.v3.oas.annotations.media.Schema;
import lombok.Data;

@Data
@TableName("file")
@Schema(description = "File entity")
public class FileEntity {

    @TableId(type = IdType.AUTO)
    @Schema(description = "Primary key")
    private Long id;

    @Schema(description = "Original filename")
    private String originalName;

    @Schema(description = "Object storage key")
    @TableField("storage_key")
    private String storageKey;

    @Schema(description = "Object storage bucket")
    @TableField("storage_bucket")
    private String storageBucket;

    @Schema(description = "Storage type")
    @TableField("storage_type")
    private String storageType;

    @Schema(description = "File size in bytes")
    private Long size;

    @Schema(description = "MIME type")
    private String mimeType;

    @Schema(description = "File md5")
    private String md5;

    @Schema(description = "Create time")
    private Long createTime;

    @Schema(description = "Update time")
    private Long updateTime;

    @TableLogic
    @Schema(description = "Deleted")
    private Boolean deleted;

    @Schema(description = "Vectorized")
    private Boolean vectorized;
}
