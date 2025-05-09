import request from '@/utils/request'
import type { ProjectVO } from '@/types/project'
import type { ApiResponse } from '@/types/response'

// 获取我的工程列表
export const getMyProjects = () => {
  return request<ApiResponse<ProjectVO[]>>({
    url: '/projects/my',
    method: 'get'
  })
}

// 创建工程
export const createProject = (data: Partial<ProjectVO>) => {
  return request<ApiResponse<ProjectVO>>({
    url: '/projects',
    method: 'post',
    data
  })
}

// 更新工程
export const updateProject = (id: number, data: Partial<ProjectVO>) => {
  return request<ApiResponse<ProjectVO>>({
    url: `/projects/${id}`,
    method: 'put',
    data
  })
}

// 删除工程
export const deleteProject = (id: number) => {
  return request<ApiResponse<void>>({
    url: `/projects/${id}`,
    method: 'delete'
  })
}

// 获取项目文件列表
export const getProjectFiles = (projectId: number) => {
  return request<ApiResponse<FileVO[]>>({
    url: `/projects/${projectId}/files`,
    method: 'get'
  })
}

// 获取项目详情
export const getProjectById = (id: number) => {
  return request<ApiResponse<ProjectVO>>({
    url: `/projects/${id}`,
    method: 'get'
  })
}

// 定义文件VO类型
export interface FileVO {
  id: number
  originalName: string
  mimeType: string
  size: number
  createTime: number
  updateTime: number
} 