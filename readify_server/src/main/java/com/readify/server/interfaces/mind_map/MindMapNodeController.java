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
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/mind-map-nodes")
@RequiredArgsConstructor
@Tag(name = "思维导图节点管理", description = "思维导图节点树查询")
public class MindMapNodeController {
    private final MindMapNodeService mindMapNodeService;
    private final MindMapNodeTreeVOConverter mindMapNodeTreeVOConverter = MindMapNodeTreeVOConverter.INSTANCE;

    @Operation(summary = "查询完整思维导图树")
    @GetMapping("/full-tree/{mindMapId}")
    @PreAuthorize("hasAuthority('MIND_MAP:READ')")
    public Result<MindMapNodeTreeVO> getFullMindMap(@Parameter(description = "思维导图ID") @PathVariable Long mindMapId) {
        MindMapNodeTree fullTree = mindMapNodeService.getFullMindMap(mindMapId, SecurityUtils.getCurrentUserId());
        return Result.success(mindMapNodeTreeVOConverter.toVO(fullTree));
    }

    @Operation(summary = "查询子树")
    @GetMapping("/sub-tree/{nodeId}")
    @PreAuthorize("hasAuthority('MIND_MAP:READ')")
    public Result<MindMapNodeTreeVO> getSubTree(@Parameter(description = "节点ID") @PathVariable Long nodeId) {
        MindMapNodeTree subTree = mindMapNodeService.getSubTreeByNodeId(nodeId, SecurityUtils.getCurrentUserId());
        return Result.success(mindMapNodeTreeVOConverter.toVO(subTree));
    }
}
