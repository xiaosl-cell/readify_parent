package com.readify.server.interfaces.mind_map;

import com.readify.server.domain.mind_map.model.MindMap;
import com.readify.server.domain.mind_map.service.MindMapService;
import com.readify.server.infrastructure.common.Result;
import com.readify.server.infrastructure.security.SecurityUtils;
import com.readify.server.interfaces.mind_map.converter.MindMapVOConverter;
import com.readify.server.interfaces.mind_map.vo.MindMapVO;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.Parameter;
import io.swagger.v3.oas.annotations.tags.Tag;
import lombok.RequiredArgsConstructor;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController
@RequestMapping("/mind-maps")
@RequiredArgsConstructor
@Tag(name = "思维导图管理", description = "思维导图相关的API接口")
public class MindMapController {
    private final MindMapService mindMapService;
    private final MindMapVOConverter mindMapVOConverter = MindMapVOConverter.INSTANCE;

    @Operation(summary = "创建思维导图")
    @PostMapping
    public Result<MindMapVO> createMindMap(@RequestBody MindMapVO mindMapVO) {
        MindMap mindMap = mindMapVOConverter.toDomain(mindMapVO);
        MindMap createdMindMap = mindMapService.createMindMap(mindMap, SecurityUtils.getCurrentUserId());
        return Result.success(mindMapVOConverter.toVO(createdMindMap));
    }

    @Operation(summary = "更新思维导图")
    @PutMapping("/{id}")
    public Result<MindMapVO> updateMindMap(
            @Parameter(description = "思维导图ID") @PathVariable Long id,
            @RequestBody MindMapVO mindMapVO) {
        MindMap mindMap = mindMapVOConverter.toDomain(mindMapVO);
        mindMap.setId(id);
        MindMap updatedMindMap = mindMapService.updateMindMap(mindMap, SecurityUtils.getCurrentUserId());
        return Result.success(mindMapVOConverter.toVO(updatedMindMap));
    }

    @Operation(summary = "获取思维导图详情")
    @GetMapping("/{id}")
    public Result<MindMapVO> getMindMapById(
            @Parameter(description = "思维导图ID") @PathVariable Long id) {
        MindMap mindMap = mindMapService.getMindMapById(id, SecurityUtils.getCurrentUserId());
        return Result.success(mindMapVOConverter.toVO(mindMap));
    }

    @Operation(summary = "获取用户所有思维导图")
    @GetMapping("/my")
    public Result<List<MindMapVO>> getMyMindMaps() {
        List<MindMap> mindMaps = mindMapService.getUserMindMaps(SecurityUtils.getCurrentUserId());
        return Result.success(mindMapVOConverter.toVOList(mindMaps));
    }

    @Operation(summary = "获取项目下所有思维导图")
    @GetMapping("/project/{projectId}")
    public Result<List<MindMapVO>> getProjectMindMaps(
            @Parameter(description = "项目ID") @PathVariable Long projectId) {
        List<MindMap> mindMaps = mindMapService.getProjectMindMaps(projectId, SecurityUtils.getCurrentUserId());
        return Result.success(mindMapVOConverter.toVOList(mindMaps));
    }

    @Operation(summary = "删除思维导图")
    @DeleteMapping("/{id}")
    public Result<Boolean> deleteMindMap(
            @Parameter(description = "思维导图ID") @PathVariable Long id) {
        boolean success = mindMapService.deleteMindMap(id, SecurityUtils.getCurrentUserId());
        return Result.success(success);
    }

    @Operation(summary = "检查思维导图标题是否已存在")
    @GetMapping("/check")
    public Result<Boolean> checkMindMapTitle(
            @Parameter(description = "思维导图标题") @RequestParam String title,
            @Parameter(description = "项目ID") @RequestParam Long projectId) {
        return Result.success(mindMapService.isMindMapTitleExists(title, projectId, SecurityUtils.getCurrentUserId()));
    }
} 