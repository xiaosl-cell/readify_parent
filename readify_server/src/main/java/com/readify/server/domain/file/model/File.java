package com.readify.server.domain.file.model;

import lombok.Builder;
import lombok.Getter;
import lombok.Setter;

@Getter
@Setter
@Builder
public class File {
    private Long id;
    private String originalName;
    private String storageKey;
    private String storageBucket;
    private String storageType;
    private Long size;
    private String mimeType;
    private String md5;
    private Long createTime;
    private Long updateTime;
    private Boolean deleted;
    private Boolean vectorized;
    private Long projectId;
    private Long userId;
} 
