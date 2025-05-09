package com.readify.server.interfaces.mind_map;

import com.readify.server.domain.mind_map.model.MindMapNodeTree;
import com.readify.server.domain.mind_map.service.MindMapNodeService;
import com.readify.server.infrastructure.common.Result;
import com.readify.server.infrastructure.security.SecurityUtils;
import com.readify.server.interfaces.mind_map.converter.MindMapNodeTreeVOConverter;
import com.readify.server.interfaces.mind_map.vo.MindMapNodeTreeVO;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.Parameter;
import io.swagger.v3.oas.annotations.tags.Tag;
import lombok.RequiredArgsConstructor;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/mind-map-nodes")
@RequiredArgsConstructor
@Tag(name = "思维导图节点管理", description = "思维导图节点相关的API接口")
public class MindMapNodeController {
    private final MindMapNodeService mindMapNodeService;
    private final MindMapNodeTreeVOConverter mindMapNodeTreeVOConverter = MindMapNodeTreeVOConverter.INSTANCE;

    @Operation(summary = "获取完整思维导图结构", description = "根据思维导图ID获取完整的思维导图树形结构")
    @GetMapping("/full-tree/{mindMapId}")
    public Result<MindMapNodeTreeVO> getFullMindMap(
            @Parameter(description = "思维导图ID") @PathVariable Long mindMapId) {
        MindMapNodeTree fullTree = mindMapNodeService.getFullMindMap(mindMapId);
        return Result.success(mindMapNodeTreeVOConverter.toVO(fullTree));
    }

    @Operation(summary = "获取节点子树", description = "根据节点ID获取以该节点为根的子树")
    @GetMapping("/sub-tree/{nodeId}")
    public Result<MindMapNodeTreeVO> getSubTree(
            @Parameter(description = "节点ID") @PathVariable Long nodeId) {
        MindMapNodeTree subTree = mindMapNodeService.getSubTreeByNodeId(nodeId);
        return Result.success(mindMapNodeTreeVOConverter.toVO(subTree));
    }
} 