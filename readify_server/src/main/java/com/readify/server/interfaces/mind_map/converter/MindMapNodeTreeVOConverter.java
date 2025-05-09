package com.readify.server.interfaces.mind_map.converter;

import com.readify.server.domain.mind_map.model.MindMapNodeTree;
import com.readify.server.interfaces.mind_map.vo.MindMapNodeTreeVO;
import org.mapstruct.Mapper;
import org.mapstruct.factory.Mappers;

@Mapper
public interface MindMapNodeTreeVOConverter {
    MindMapNodeTreeVOConverter INSTANCE = Mappers.getMapper(MindMapNodeTreeVOConverter.class);

    MindMapNodeTreeVO toVO(MindMapNodeTree tree);
    
    MindMapNodeTree toDomain(MindMapNodeTreeVO vo);
} 