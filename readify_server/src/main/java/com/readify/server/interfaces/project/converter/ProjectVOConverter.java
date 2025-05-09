package com.readify.server.interfaces.project.converter;

import com.readify.server.domain.project.model.Project;
import com.readify.server.interfaces.project.vo.ProjectVO;
import org.mapstruct.Mapper;
import org.mapstruct.MappingTarget;
import org.mapstruct.factory.Mappers;

import java.util.List;

@Mapper
public interface ProjectVOConverter {
    ProjectVOConverter INSTANCE = Mappers.getMapper(ProjectVOConverter.class);

    ProjectVO toVO(Project project);

    Project toDomain(ProjectVO projectVO);

    List<ProjectVO> toVOList(List<Project> projects);

    void updateProjectVO(Project project, @MappingTarget ProjectVO projectVO);
} 