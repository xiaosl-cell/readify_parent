package com.readify.server.interfaces.project;

import com.readify.server.domain.project.model.Project;
import com.readify.server.domain.project.service.ProjectService;
import com.readify.server.infrastructure.common.Result;
import com.readify.server.infrastructure.security.SecurityUtils;
import com.readify.server.interfaces.project.converter.ProjectVOConverter;
import com.readify.server.interfaces.project.vo.ProjectVO;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.Parameter;
import io.swagger.v3.oas.annotations.tags.Tag;
import lombok.RequiredArgsConstructor;
import org.springframework.web.bind.annotation.*;

import java.util.List;
import java.util.concurrent.ThreadPoolExecutor;

@RestController
@RequestMapping("/projects")
@RequiredArgsConstructor
@Tag(name = "工程管理", description = "工程相关的API接口")
public class ProjectController {
    private final ProjectService projectService;
    private final ProjectVOConverter projectVOConverter = ProjectVOConverter.INSTANCE;

    @Operation(summary = "创建工程")
    @PostMapping
    public Result<ProjectVO> createProject(@RequestBody ProjectVO projectVO) {
        Project project = projectVOConverter.toDomain(projectVO);
        Project createdProject = projectService.createProject(project, SecurityUtils.getCurrentUserId());
        return Result.success(projectVOConverter.toVO(createdProject));
    }

    @Operation(summary = "更新工程信息")
    @PutMapping("/{id}")
    public Result<ProjectVO> updateProject(
            @Parameter(description = "工程ID") @PathVariable Long id,
            @RequestBody ProjectVO projectVO) {
        Project project = projectVOConverter.toDomain(projectVO);
        project.setId(id);
        Project updatedProject = projectService.updateProject(project, SecurityUtils.getCurrentUserId());
        return Result.success(projectVOConverter.toVO(updatedProject));
    }

    @Operation(summary = "删除工程")
    @DeleteMapping("/{id}")
    public Result<Void> deleteProject(
            @Parameter(description = "工程ID") @PathVariable Long id) {
        projectService.deleteProject(id, SecurityUtils.getCurrentUserId());
        return Result.success();
    }

    @Operation(summary = "根据ID获取工程信息")
    @GetMapping("/{id}")
    public Result<ProjectVO> getProjectById(
            @Parameter(description = "工程ID") @PathVariable Long id) {
        Project project = projectService.getProjectById(id, SecurityUtils.getCurrentUserId());
        return Result.success(projectVOConverter.toVO(project));
    }

    @Operation(summary = "根据名称获取工程信息")
    @GetMapping("/name/{name}")
    public Result<ProjectVO> getProjectByName(
            @Parameter(description = "工程名称") @PathVariable String name) {
        Project project = projectService.getProjectByName(name, SecurityUtils.getCurrentUserId());
        return Result.success(projectVOConverter.toVO(project));
    }

    @Operation(summary = "获取所有工程列表")
    @GetMapping
    public Result<List<ProjectVO>> getAllProjects() {
        List<Project> projects = projectService.getAllProjects();
        return Result.success(projectVOConverter.toVOList(projects));
    }

    @Operation(summary = "获取我的工程列表")
    @GetMapping("/my")
    public Result<List<ProjectVO>> getMyProjects() {
        List<Project> projects = projectService.getUserProjects(SecurityUtils.getCurrentUserId());
        return Result.success(projectVOConverter.toVOList(projects));
    }

    @Operation(summary = "检查工程名称是否已存在")
    @GetMapping("/check/{name}")
    public Result<Boolean> checkProjectName(
            @Parameter(description = "工程名称") @PathVariable String name) {
        return Result.success(projectService.isProjectNameExists(name, SecurityUtils.getCurrentUserId()));
    }
} 