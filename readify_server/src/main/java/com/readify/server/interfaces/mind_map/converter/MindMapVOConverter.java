package com.readify.server.interfaces.mind_map.converter;

import com.readify.server.domain.mind_map.model.MindMap;
import com.readify.server.interfaces.mind_map.vo.MindMapVO;
import org.mapstruct.Mapper;
import org.mapstruct.MappingTarget;
import org.mapstruct.factory.Mappers;

import java.util.List;

@Mapper
public interface MindMapVOConverter {
    MindMapVOConverter INSTANCE = Mappers.getMapper(MindMapVOConverter.class);

    MindMapVO toVO(MindMap mindMap);

    MindMap toDomain(MindMapVO mindMapVO);

    List<MindMapVO> toVOList(List<MindMap> mindMaps);

    void updateMindMapVO(MindMap mindMap, @MappingTarget MindMapVO mindMapVO);
} 