package com.readify.server.domain.file.repository;

import com.readify.server.domain.file.model.File;

import java.io.InputStream;
import java.util.List;
import java.util.Optional;

public interface FileRepository {
    /**
     * 保存文件信息
     */
    File save(File file);

    /**
     * 根据ID查找文件
     */
    Optional<File> findById(Long id);

    /**
     * 根据ID列表查找文件
     */
    List<File> findAllById(List<Long> ids);

    /**
     * 根据MD5查找文件
     */
    Optional<File> findByMd5(String md5);

    /**
     * 根据ID删除文件
     */
    void deleteById(Long id);

    /**
     * 上传文件
     */
    File upload(String originalFilename, String mimeType, long size, InputStream inputStream);

    /**
     * 删除物理文件
     */
    void deletePhysicalFile(String storageName);

    /**
     * 更新文件向量化状态
     *
     * @param fileId 文件ID
     * @param vectorized 是否已向量化
     * @return 更新后的文件信息
     */
    File updateVectorizedStatus(Long fileId, Boolean vectorized);

    /**
     * 查找未向量化的文件
     *
     * @return 未向量化的文件列表
     */
    List<File> findNonVectorizedFiles();
} 