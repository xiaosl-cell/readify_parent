package com.readify.server.interfaces.file;

import com.readify.server.domain.file.model.File;
import com.readify.server.domain.file.service.FileService;
import com.readify.server.domain.project.service.ProjectFileService;
import com.readify.server.infrastructure.common.Result;
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
import org.springframework.web.bind.annotation.*;
import org.springframework.web.multipart.MultipartFile;

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
@Tag(name = "文件管理", description = "文件管理相关接口")
public class FileController {
    private final FileService fileService;
    private final FileStorage fileStorage;
    private final ProjectFileService projectFileService;
    private final WebSocketSessionManager webSocketSessionManager;

    @GetMapping("/{fileId}")
    @Operation(summary = "获取文件信息")
    public Result<FileVO> getFileInfo(@PathVariable Long fileId) {
        File file = fileService.getFileInfo(fileId);
        return Result.success(FileVO.from(file));
    }

    @GetMapping("/{fileId}/download")
    @Operation(summary = "下载文件")
    public void download(
            @Parameter(description = "文件ID") @PathVariable Long fileId,
            HttpServletResponse response) throws IOException {
        File file = fileService.getFileInfo(fileId);

        response.setContentType(file.getMimeType());
        response.setContentLength(Math.toIntExact(file.getSize()));
        response.setHeader(HttpHeaders.CONTENT_DISPOSITION, "attachment; filename*=UTF-8''" +
                URLEncoder.encode(file.getOriginalName(), StandardCharsets.UTF_8));

        try (InputStream inputStream = fileStorage.retrieve(file.getStorageName());
                OutputStream outputStream = response.getOutputStream()) {
            // 使用缓冲区复制流
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
    public Result<Void> delete(
            @Parameter(description = "文件ID") @PathVariable Long fileId) {
        fileService.delete(fileId);
        return Result.success();
    }

    @PostMapping("/vectorized")
    @Operation(summary = "向量化完成通知")
    public Result<Void> vectorizedCompleted(@RequestBody VectorizedCallbackReq req) {
        log.info("收到向量化完成通知：{}", req);
        if (!Boolean.TRUE.equals(req.getSuccess()))
            return Result.success("接收成功");
        File file = fileService.getFileInfo(req.getFileId());

        // 获取项目文件列表
        List<File> projectFiles = projectFileService.getProjectFiles(file.getProjectId());
        List<FileVO> fileVOs = projectFiles.stream()
                .map(FileVO::from)
                .collect(Collectors.toList());

        // 发送WebSocket通知
        if (webSocketSessionManager.getUserSessionId(file.getUserId()) != null) {
            WebSocketMessage<List<FileVO>> message = WebSocketMessage.create(
                    "projectFiles",
                    fileVOs);
            webSocketSessionManager.sendMessageToUser(file.getUserId(), message);
            log.info("已发送WebSocket通知给用户：{}", file.getUserId());
        }

        return Result.success();
    }

    private java.io.InputStream getInputStream(MultipartFile file) {
        try {
            return file.getInputStream();
        } catch (java.io.IOException e) {
            throw new RuntimeException("Failed to get input stream from file", e);
        }
    }
}