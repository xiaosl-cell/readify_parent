package com.readify.server.domain.project.service.impl;

import com.readify.server.domain.file.model.File;
import com.readify.server.domain.file.service.FileService;
import com.readify.server.domain.project.model.Project;
import com.readify.server.domain.project.model.ProjectFile;
import com.readify.server.domain.project.repository.ProjectFileRepository;
import com.readify.server.domain.project.service.ProjectFileService;
import com.readify.server.domain.project.service.ProjectService;
import com.readify.server.infrastructure.common.exception.NotFoundException;
import com.readify.server.infrastructure.security.SecurityUtils;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.MediaType;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.multipart.MultipartFile;
import org.springframework.web.reactive.function.client.WebClient;
import reactor.core.publisher.Mono;
import reactor.core.scheduler.Schedulers;

import java.util.Collections;
import java.util.List;
import java.util.stream.Collectors;

@Slf4j
@Service
@RequiredArgsConstructor
public class ProjectFileServiceImpl implements ProjectFileService {
    private final FileService fileService;
    private final ProjectService projectService;
    private final ProjectFileRepository projectFileRepository;
    private final WebClient vectorServiceClient;

    @Override
    @Transactional
    public File uploadAndAssociateFile(Long projectId, MultipartFile file) {
        // 验证项目是否存在
        Long currentUserId = SecurityUtils.getCurrentUserId();
        Project project = projectService.getProjectById(projectId, currentUserId);
        if (project == null) {
            throw new NotFoundException("项目不存在");
        }

        // 上传文件
        File uploadedFile = fileService.upload(
                file.getOriginalFilename(),
                file.getContentType(),
                file.getSize(),
                getInputStream(file));

        // 创建项目文件关联
        ProjectFile projectFile = ProjectFile.builder()
                .projectId(projectId)
                .userId(SecurityUtils.getCurrentUserId())
                .fileId(uploadedFile.getId())
                .createTime(System.currentTimeMillis())
                .updateTime(System.currentTimeMillis())
                .deleted(false)
                .build();

        projectFileRepository.save(projectFile);

        // 异步发送文件处理请求
        sendProcessRequest(uploadedFile.getId())
                .subscribeOn(Schedulers.boundedElastic())
                .subscribe(
                        response -> log.info("文件处理请求发送成功：fileId={}", uploadedFile.getId()),
                        error -> log.error("文件处理请求发送失败：fileId={}, error={}", uploadedFile.getId(), error.getMessage()));

        return uploadedFile;
    }

    private Mono<Void> sendProcessRequest(Long fileId) {
        return vectorServiceClient.post()
                .uri("/api/v1/files/{fileId}/process", fileId)
                .contentType(java.util.Objects.requireNonNull(MediaType.APPLICATION_JSON))
                .retrieve()
                .bodyToMono(Void.class)
                .doOnError(error -> log.error("发送文件处理请求失败：fileId={}, error={}", fileId, error.getMessage()));
    }

    private java.io.InputStream getInputStream(MultipartFile file) {
        try {
            return file.getInputStream();
        } catch (java.io.IOException e) {
            throw new RuntimeException("Failed to get input stream from file", e);
        }
    }

    @Override
    public List<File> getProjectFiles(Long projectId) {
        projectService.getProjectById(projectId, SecurityUtils.getCurrentUserId());
        List<ProjectFile> projectFiles = projectFileRepository.findByProjectId(projectId);
        List<Long> fileIds = projectFiles.stream().map(ProjectFile::getFileId).collect(Collectors.toList());
        if (fileIds.isEmpty()) {
            return Collections.emptyList();
        }
        return fileService.getFilesByIds(fileIds);
    }
}
