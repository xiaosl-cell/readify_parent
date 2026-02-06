package com.readify.server.domain.file.service;

import com.readify.server.domain.file.model.File;

import java.io.InputStream;
import java.util.List;

public interface FileService {
    File upload(String originalFilename, String mimeType, long size, InputStream inputStream);
    void delete(Long fileId, Long userId);
    File getFileInfo(Long fileId, Long userId);
    List<File> getFilesByIds(List<Long> fileIds);

    /**
     * 更新文件向量化状态
     *
     * @param fileId 文件ID
     * @param vectorized 是否已向量化
     * @return 更新后的文件信息
     */
    File updateVectorizedStatus(Long fileId, Boolean vectorized);

    /**
     * 获取未向量化的文件列表
     *
     * @return 未向量化的文件列表
     */
    List<File> getNonVectorizedFiles();
}
