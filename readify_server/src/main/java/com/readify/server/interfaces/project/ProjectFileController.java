package com.readify.server.interfaces.project;

import com.readify.server.domain.file.model.File;
import com.readify.server.domain.project.service.ProjectFileService;
import com.readify.server.infrastructure.common.Result;
import com.readify.server.infrastructure.security.SecurityUtils;
import com.readify.server.interfaces.file.vo.FileVO;
import com.readify.server.websocket.WebSocketSessionManager;
import com.readify.server.websocket.message.WebSocketMessage;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.Parameter;
import io.swagger.v3.oas.annotations.tags.Tag;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.multipart.MultipartFile;

import java.util.List;
import java.util.stream.Collectors;

@Slf4j
@RestController
@RequestMapping("/projects")
@RequiredArgsConstructor
@Tag(name = "项目文件管理", description = "项目文件管理相关接口")
public class ProjectFileController {
    private final ProjectFileService projectFileService;
    private final WebSocketSessionManager webSocketSessionManager;

    @PostMapping("/{projectId}/files")
    @Operation(summary = "上传文件并关联到项目")
    public Result<FileVO> uploadAndAssociateFile(
            @Parameter(description = "项目ID") @PathVariable Long projectId,
            @Parameter(description = "文件") @RequestParam("file") MultipartFile file) {
        File uploadedFile = projectFileService.uploadAndAssociateFile(projectId, file);


        // 发送WebSocket通知
        Long currentUserId = SecurityUtils.getCurrentUserId();
        if (webSocketSessionManager.isUserOnline(currentUserId)) {

            // 获取项目文件列表
            List<File> projectFiles = projectFileService.getProjectFiles(projectId);
            List<FileVO> fileVOs = projectFiles.stream()
                    .map(FileVO::from)
                    .collect(Collectors.toList());

            WebSocketMessage<List<FileVO>> message = WebSocketMessage.create(
                    "projectFiles",
                    fileVOs
            );
            webSocketSessionManager.sendMessageToUser(currentUserId, message);
            log.info("已发送WebSocket通知给用户：{}", currentUserId);
        }
        return Result.success(FileVO.from(uploadedFile));
    }

    @GetMapping("/{projectId}/files")
    @Operation(summary = "获取项目文件列表")
    public Result<List<FileVO>> getProjectFiles(
            @Parameter(description = "项目ID") @PathVariable Long projectId) {
        List<File> files = projectFileService.getProjectFiles(projectId);
        return Result.success(files.stream().map(FileVO::from).collect(Collectors.toList()));
    }
} 