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
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.web.bind.annotation.DeleteMapping;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.PutMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

import java.util.List;

@RestController
@RequestMapping("/mind-maps")
@RequiredArgsConstructor
@Tag(name = "思维导图管理", description = "思维导图创建、查询与维护")
public class MindMapController {
    private final MindMapService mindMapService;
    private final MindMapVOConverter mindMapVOConverter = MindMapVOConverter.INSTANCE;

    @Operation(summary = "创建思维导图")
    @PostMapping
    @PreAuthorize("hasAuthority('MIND_MAP:WRITE')")
    public Result<MindMapVO> createMindMap(@RequestBody MindMapVO mindMapVO) {
        MindMap mindMap = mindMapVOConverter.toDomain(mindMapVO);
        MindMap createdMindMap = mindMapService.createMindMap(mindMap, SecurityUtils.getCurrentUserId());
        return Result.success(mindMapVOConverter.toVO(createdMindMap));
    }

    @Operation(summary = "更新思维导图")
    @PutMapping("/{id}")
    @PreAuthorize("hasAuthority('MIND_MAP:WRITE')")
    public Result<MindMapVO> updateMindMap(
            @Parameter(description = "思维导图ID") @PathVariable Long id,
            @RequestBody MindMapVO mindMapVO) {
        MindMap mindMap = mindMapVOConverter.toDomain(mindMapVO);
        mindMap.setId(id);
        MindMap updatedMindMap = mindMapService.updateMindMap(mindMap, SecurityUtils.getCurrentUserId());
        return Result.success(mindMapVOConverter.toVO(updatedMindMap));
    }

    @Operation(summary = "查询思维导图详情")
    @GetMapping("/{id}")
    @PreAuthorize("hasAuthority('MIND_MAP:READ')")
    public Result<MindMapVO> getMindMapById(@Parameter(description = "思维导图ID") @PathVariable Long id) {
        MindMap mindMap = mindMapService.getMindMapById(id, SecurityUtils.getCurrentUserId());
        return Result.success(mindMapVOConverter.toVO(mindMap));
    }

    @Operation(summary = "查询我的思维导图")
    @GetMapping("/my")
    @PreAuthorize("hasAuthority('MIND_MAP:READ')")
    public Result<List<MindMapVO>> getMyMindMaps() {
        List<MindMap> mindMaps = mindMapService.getUserMindMaps(SecurityUtils.getCurrentUserId());
        return Result.success(mindMapVOConverter.toVOList(mindMaps));
    }

    @Operation(summary = "查询项目下思维导图")
    @GetMapping("/project/{projectId}")
    @PreAuthorize("hasAuthority('MIND_MAP:READ')")
    public Result<List<MindMapVO>> getProjectMindMaps(@Parameter(description = "项目ID") @PathVariable Long projectId) {
        List<MindMap> mindMaps = mindMapService.getProjectMindMaps(projectId, SecurityUtils.getCurrentUserId());
        return Result.success(mindMapVOConverter.toVOList(mindMaps));
    }

    @Operation(summary = "删除思维导图")
    @DeleteMapping("/{id}")
    @PreAuthorize("hasAuthority('MIND_MAP:WRITE')")
    public Result<Boolean> deleteMindMap(@Parameter(description = "思维导图ID") @PathVariable Long id) {
        boolean success = mindMapService.deleteMindMap(id, SecurityUtils.getCurrentUserId());
        return Result.success(success);
    }

    @Operation(summary = "检查思维导图标题")
    @GetMapping("/check")
    @PreAuthorize("hasAuthority('MIND_MAP:READ')")
    public Result<Boolean> checkMindMapTitle(
            @Parameter(description = "标题") @RequestParam String title,
            @Parameter(description = "项目ID") @RequestParam Long projectId) {
        return Result.success(mindMapService.isMindMapTitleExists(title, projectId, SecurityUtils.getCurrentUserId()));
    }
}

