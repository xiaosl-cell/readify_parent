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
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.web.bind.annotation.DeleteMapping;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.PutMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.List;

@RestController
@RequestMapping("/projects")
@RequiredArgsConstructor
@Tag(name = "项目管理", description = "项目相关API")
public class ProjectController {
    private final ProjectService projectService;
    private final ProjectVOConverter projectVOConverter = ProjectVOConverter.INSTANCE;

    @Operation(summary = "创建项目")
    @PostMapping
    @PreAuthorize("hasAuthority('PROJECT:WRITE')")
    public Result<ProjectVO> createProject(@RequestBody ProjectVO projectVO) {
        Project project = projectVOConverter.toDomain(projectVO);
        Project createdProject = projectService.createProject(project, SecurityUtils.getCurrentUserId());
        return Result.success(projectVOConverter.toVO(createdProject));
    }

    @Operation(summary = "更新项目")
    @PutMapping("/{id}")
    @PreAuthorize("hasAuthority('PROJECT:WRITE')")
    public Result<ProjectVO> updateProject(
            @Parameter(description = "项目ID") @PathVariable Long id,
            @RequestBody ProjectVO projectVO) {
        Project project = projectVOConverter.toDomain(projectVO);
        project.setId(id);
        Project updatedProject = projectService.updateProject(project, SecurityUtils.getCurrentUserId());
        return Result.success(projectVOConverter.toVO(updatedProject));
    }

    @Operation(summary = "删除项目")
    @DeleteMapping("/{id}")
    @PreAuthorize("hasAuthority('PROJECT:WRITE')")
    public Result<Void> deleteProject(@Parameter(description = "项目ID") @PathVariable Long id) {
        projectService.deleteProject(id, SecurityUtils.getCurrentUserId());
        return Result.success();
    }

    @Operation(summary = "按ID查看项目")
    @GetMapping("/{id}")
    @PreAuthorize("hasAuthority('PROJECT:READ')")
    public Result<ProjectVO> getProjectById(@Parameter(description = "项目ID") @PathVariable Long id) {
        Project project = projectService.getProjectById(id, SecurityUtils.getCurrentUserId());
        return Result.success(projectVOConverter.toVO(project));
    }

    @Operation(summary = "按名称查看项目")
    @GetMapping("/name/{name}")
    @PreAuthorize("hasAuthority('PROJECT:READ')")
    public Result<ProjectVO> getProjectByName(@Parameter(description = "项目名称") @PathVariable String name) {
        Project project = projectService.getProjectByName(name, SecurityUtils.getCurrentUserId());
        return Result.success(projectVOConverter.toVO(project));
    }

    @Operation(summary = "查看全部项目")
    @GetMapping
    @PreAuthorize("hasRole('ADMIN')")
    public Result<List<ProjectVO>> getAllProjects() {
        List<Project> projects = projectService.getAllProjects();
        return Result.success(projectVOConverter.toVOList(projects));
    }

    @Operation(summary = "查看我的项目")
    @GetMapping("/my")
    @PreAuthorize("hasAuthority('PROJECT:READ')")
    public Result<List<ProjectVO>> getMyProjects() {
        List<Project> projects = projectService.getUserProjects(SecurityUtils.getCurrentUserId());
        return Result.success(projectVOConverter.toVOList(projects));
    }

    @Operation(summary = "检查项目名是否存在")
    @GetMapping("/check/{name}")
    @PreAuthorize("hasAuthority('PROJECT:READ')")
    public Result<Boolean> checkProjectName(@Parameter(description = "项目名称") @PathVariable String name) {
        return Result.success(projectService.isProjectNameExists(name, SecurityUtils.getCurrentUserId()));
    }
}

