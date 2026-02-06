import api from './index'
import type { Result, UserWithRoles, Role, DashboardStats } from '@/types'

export const getUsersWithRoles = (): Promise<Result<UserWithRoles[]>> => {
  return api.get('/admin/users')
}

export const getUserRoles = (id: number): Promise<Result<Role[]>> => {
  return api.get(`/admin/users/${id}/roles`)
}

export const assignRolesToUser = (id: number, roleIds: number[]): Promise<Result<void>> => {
  return api.post(`/admin/users/${id}/roles`, { roleIds })
}

export const getDashboardStats = (): Promise<Result<DashboardStats>> => {
  return api.get('/admin/users/stats')
}
