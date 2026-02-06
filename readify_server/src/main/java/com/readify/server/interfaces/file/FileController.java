package com.readify.server.interfaces.file;

import com.readify.server.domain.file.model.File;
import com.readify.server.domain.file.service.FileService;
import com.readify.server.domain.project.service.ProjectFileService;
import com.readify.server.infrastructure.common.Result;
import com.readify.server.infrastructure.security.SecurityUtils;
import com.readify.server.infrastructure.utils.file.FileStorage;
import com.readify.server.interfaces.file.req.VectorizedCallbackReq;
import com.readify.server.interfaces.file.vo.FileVO;
import com.readify.server.websocket.WebSocketSessionManager;
import com.readify.server.websocket.message.WebSocketMessage;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.Parameter;
import io.swagger.v3.oas.annotations.tags.Tag;
import jakarta.servlet.http.HttpServletResponse;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.HttpHeaders;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.web.bind.annotation.DeleteMapping;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.io.IOException;
import java.io.InputStream;
import java.io.OutputStream;
import java.net.URLEncoder;
import java.nio.charset.StandardCharsets;
import java.util.List;
import java.util.stream.Collectors;

@Slf4j
@RestController
@RequestMapping("/files")
@RequiredArgsConstructor
@Tag(name = "文件管理", description = "文件查询、下载与回调")
public class FileController {
    private final FileService fileService;
    private final FileStorage fileStorage;
    private final ProjectFileService projectFileService;
    private final WebSocketSessionManager webSocketSessionManager;

    @GetMapping("/{fileId}")
    @Operation(summary = "获取文件信息")
    @PreAuthorize("hasAuthority('FILE:READ')")
    public Result<FileVO> getFileInfo(@PathVariable Long fileId) {
        File file = fileService.getFileInfo(fileId, SecurityUtils.getCurrentUserId());
        return Result.success(FileVO.from(file));
    }

    @GetMapping("/{fileId}/download")
    @Operation(summary = "下载文件")
    @PreAuthorize("hasAuthority('FILE:READ')")
    public void download(@Parameter(description = "文件ID") @PathVariable Long fileId,
                         HttpServletResponse response) throws IOException {
        File file = fileService.getFileInfo(fileId, SecurityUtils.getCurrentUserId());

        response.setContentType(file.getMimeType());
        response.setContentLength(Math.toIntExact(file.getSize()));
        response.setHeader(HttpHeaders.CONTENT_DISPOSITION,
                "attachment; filename*=UTF-8''" + URLEncoder.encode(file.getOriginalName(), StandardCharsets.UTF_8));

        try (InputStream inputStream = fileStorage.retrieve(file.getStorageBucket(), file.getStorageKey());
             OutputStream outputStream = response.getOutputStream()) {
            byte[] buffer = new byte[4096];
            int bytesRead;
            while ((bytesRead = inputStream.read(buffer)) != -1) {
                outputStream.write(buffer, 0, bytesRead);
            }
            outputStream.flush();
        } catch (Exception e) {
            log.warn(e.getMessage());
        }
    }

    @DeleteMapping("/{fileId}")
    @Operation(summary = "删除文件")
    @PreAuthorize("hasAuthority('FILE:WRITE')")
    public Result<Void> delete(@Parameter(description = "文件ID") @PathVariable Long fileId) {
        fileService.delete(fileId, SecurityUtils.getCurrentUserId());
        return Result.success();
    }

    @PostMapping("/vectorized")
    @Operation(summary = "向量化完成回调")
    @PreAuthorize("hasRole('ADMIN')")
    public Result<Void> vectorizedCompleted(@RequestBody VectorizedCallbackReq req) {
        log.info("Received vectorized callback: {}", req);
        if (!Boolean.TRUE.equals(req.getSuccess())) {
            return Result.success("接收成功");
        }
        File file = fileService.getFileInfo(req.getFileId(), SecurityUtils.getCurrentUserId());

        List<File> projectFiles = projectFileService.getProjectFiles(file.getProjectId());
        List<FileVO> fileVOs = projectFiles.stream().map(FileVO::from).collect(Collectors.toList());

        if (webSocketSessionManager.getUserSessionId(file.getUserId()) != null) {
            WebSocketMessage<List<FileVO>> message = WebSocketMessage.create("projectFiles", fileVOs);
            webSocketSessionManager.sendMessageToUser(file.getUserId(), message);
            log.info("WebSocket notify vectorized finished, userId={}", file.getUserId());
        }
        return Result.success();
    }
}
