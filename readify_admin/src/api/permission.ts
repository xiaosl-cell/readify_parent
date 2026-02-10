import api from './index'
import type { Result, Permission, PageResult, PermissionTree } from '@/types'

export const getPermissionsPage = (page: number, size: number, keyword?: string): Promise<Result<PageResult<Permission>>> => {
  return api.get('/admin/permissions', { params: { page, size, keyword } })
}

export const getAllPermissions = (): Promise<Result<Permission[]>> => {
  return api.get('/admin/permissions/all')
}

export const getPermissionTree = (): Promise<Result<PermissionTree>> => {
  return api.get('/admin/permissions/tree')
}

export const getPermissionById = (id: number): Promise<Result<Permission>> => {
  return api.get(`/admin/permissions/${id}`)
}

export const createPermission = (data: Partial<Permission>): Promise<Result<Permission>> => {
  return api.post('/admin/permissions', data)
}

export const updatePermission = (id: number, data: Partial<Permission>): Promise<Result<Permission>> => {
  return api.put(`/admin/permissions/${id}`, data)
}

export const deletePermission = (id: number): Promise<Result<void>> => {
  return api.delete(`/admin/permissions/${id}`)
}
