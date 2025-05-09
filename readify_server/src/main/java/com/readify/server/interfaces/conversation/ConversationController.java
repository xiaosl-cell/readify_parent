package com.readify.server.interfaces.conversation;

import com.readify.server.domain.conversation.service.ConversationService;
import com.readify.server.infrastructure.common.Result;
import com.readify.server.interfaces.conversation.vo.ConversationVO;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.Parameter;
import io.swagger.v3.oas.annotations.media.Content;
import io.swagger.v3.oas.annotations.media.Schema;
import io.swagger.v3.oas.annotations.responses.ApiResponse;
import io.swagger.v3.oas.annotations.tags.Tag;
import lombok.RequiredArgsConstructor;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.List;

@RestController
@RequestMapping("/conversation")
@RequiredArgsConstructor
@Tag(name = "对话管理", description = "对话历史记录及思考过程相关接口")
public class ConversationController {

    private final ConversationService conversationService;

    /**
     * 根据项目ID获取对话历史，包含用户消息关联的思考过程
     *
     * @param projectId 项目ID
     * @return 对话历史列表
     */
    @GetMapping("/project/{projectId}")
    @Operation(
        summary = "获取项目对话记录",
        description = "根据项目ID获取对话历史记录，包含用户消息关联的AI思考过程",
        responses = {
            @ApiResponse(
                responseCode = "200",
                description = "成功获取对话记录",
                content = @Content(
                    mediaType = "application/json",
                    schema = @Schema(implementation = Result.class)
                )
            ),
            @ApiResponse(
                responseCode = "404",
                description = "项目不存在",
                content = @Content(
                    mediaType = "application/json",
                    schema = @Schema(implementation = Result.class)
                )
            )
        }
    )
    public Result<List<ConversationVO>> getConversationsByProjectId(
        @Parameter(description = "项目ID", required = true) 
        @PathVariable Long projectId
    ) {
        List<ConversationVO> conversations = conversationService.getConversationsByProjectId(projectId);
        return Result.success(conversations);
    }
} 