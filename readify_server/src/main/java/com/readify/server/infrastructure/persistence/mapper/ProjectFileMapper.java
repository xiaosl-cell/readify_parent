package com.readify.server.infrastructure.persistence.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.readify.server.infrastructure.persistence.entity.ProjectFileEntity;
import org.apache.ibatis.annotations.Mapper;

@Mapper
public interface ProjectFileMapper extends BaseMapper<ProjectFileEntity> {
} 