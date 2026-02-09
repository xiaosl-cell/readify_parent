package com.readify.server.domain.project.service;

import com.readify.server.domain.file.model.File;
import org.springframework.web.multipart.MultipartFile;

import java.util.List;

public interface ProjectFileService {
    /**
     * 上传文件并关联到项目
     *
     * @param projectId 项目ID
     * @param file 上传的文件
     * @return 文件信息
     */
    File uploadAndAssociateFile(Long projectId, MultipartFile file);

    /**
     * 获取项目文件列表
     *
     * @param projectId 项目ID
     * @return 文件列表
     */
    List<File> getProjectFiles(Long projectId);

    /**
     * 获取项目文件列表
     *
     * @param projectId 项目ID
     * @param userId 用户ID
     * @return 文件列表
     */
    List<File> getProjectFiles(Long projectId, Long userId);
}
