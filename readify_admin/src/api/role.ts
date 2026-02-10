import api from './index'
import type { Result, Role, PageResult } from '@/types'

export const getRolesPage = (page: number, size: number, keyword?: string): Promise<Result<PageResult<Role>>> => {
  return api.get('/admin/roles', { params: { page, size, keyword } })
}

export const getAllRoles = (): Promise<Result<Role[]>> => {
  return api.get('/admin/roles/all')
}

export const getRoleById = (id: number): Promise<Result<Role>> => {
  return api.get(`/admin/roles/${id}`)
}

export const createRole = (data: Partial<Role>): Promise<Result<Role>> => {
  return api.post('/admin/roles', data)
}

export const updateRole = (id: number, data: Partial<Role>): Promise<Result<Role>> => {
  return api.put(`/admin/roles/${id}`, data)
}

export const deleteRole = (id: number): Promise<Result<void>> => {
  return api.delete(`/admin/roles/${id}`)
}

export const getRolePermissions = (id: number): Promise<Result<import('@/types').Permission[]>> => {
  return api.get(`/admin/roles/${id}/permissions`)
}

export const assignPermissionsToRole = (id: number, permissionIds: number[]): Promise<Result<void>> => {
  return api.post(`/admin/roles/${id}/permissions`, { permissionIds })
}
