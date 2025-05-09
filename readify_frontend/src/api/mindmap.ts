import request from '@/utils/request'
import type { ApiResponse } from '@/types/response'
import type { MindMapVO } from '@/types/mindmap'
import type { MindMapNodeTreeVO } from '@/types/mindmap-node'

// 创建思维导图
export const createMindMap = (data: Partial<MindMapVO>) => {
  return request<ApiResponse<MindMapVO>>({
    url: '/mind-maps',
    method: 'post',
    data
  })
}

// 获取思维导图详情
export const getMindMapById = (id: number) => {
  return request<ApiResponse<MindMapVO>>({
    url: `/mind-maps/${id}`,
    method: 'get'
  })
}

// 更新思维导图
export const updateMindMap = (id: number, data: Partial<MindMapVO>) => {
  return request<ApiResponse<MindMapVO>>({
    url: `/mind-maps/${id}`,
    method: 'put',
    data
  })
}

// 删除思维导图
export const deleteMindMap = (id: number) => {
  return request<ApiResponse<boolean>>({
    url: `/mind-maps/${id}`,
    method: 'delete'
  })
}

// 获取项目下所有思维导图
export const getProjectMindMaps = (projectId: number) => {
  return request<ApiResponse<MindMapVO[]>>({
    url: `/mind-maps/project/${projectId}`,
    method: 'get'
  })
}

// 获取用户所有思维导图
export const getMyMindMaps = () => {
  return request<ApiResponse<MindMapVO[]>>({
    url: '/mind-maps/my',
    method: 'get'
  })
}

// 检查思维导图标题是否已存在
export const checkMindMapTitle = (title: string, projectId: number) => {
  return request<ApiResponse<boolean>>({
    url: '/mind-maps/check',
    method: 'get',
    params: { title, projectId }
  })
}

// 获取完整思维导图结构
export const getFullMindMap = (mindMapId: number) => {
  return request<ApiResponse<MindMapNodeTreeVO>>({
    url: `/mind-map-nodes/full-tree/${mindMapId}`,
    method: 'get'
  })
}

// 获取节点子树
export const getNodeSubTree = (nodeId: number) => {
  return request<ApiResponse<MindMapNodeTreeVO>>({
    url: `/mind-map-nodes/sub-tree/${nodeId}`,
    method: 'get'
  })
} 