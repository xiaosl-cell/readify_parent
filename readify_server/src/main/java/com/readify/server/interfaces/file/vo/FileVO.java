package com.readify.server.interfaces.file.vo;

import com.readify.server.domain.file.model.File;
import lombok.Builder;
import lombok.Data;

@Data
@Builder
public class FileVO {
    private Long id;
    private String originalName;
    private String mimeType;
    private Long size;
    private Long createTime;
    private Long updateTime;
    private Boolean vectorized;

    public static FileVO from(File file) {
        return FileVO.builder()
                .id(file.getId())
                .originalName(file.getOriginalName())
                .mimeType(file.getMimeType())
                .size(file.getSize())
                .createTime(file.getCreateTime())
                .updateTime(file.getUpdateTime())
                .vectorized(file.getVectorized())
                .build();
    }
} 