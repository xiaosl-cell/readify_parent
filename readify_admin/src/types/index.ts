export interface Role {
  id: number
  code: string
  name: string
  description: string
  enabled: boolean
  createTime: number
  updateTime: number
}

export interface Permission {
  id: number
  code: string
  name: string
  module: string
  description: string
  enabled: boolean
  createTime: number
  updateTime: number
}

export interface User {
  id: number
  username: string
  email: string
  nickname: string
  createTime: number
}

export interface UserWithRoles extends User {
  roles: Role[]
}

export interface PageResult<T> {
  items: T[]
  total: number
  page: number
  size: number
  totalPages: number
}

export interface Result<T> {
  code: string | number
  message: string
  data: T
}

export interface DashboardStats {
  userCount: number
  roleCount: number
  permissionCount: number
}

export interface PermissionTree {
  tree: Record<string, Permission[]>
}

export interface LoginForm {
  username: string
  password: string
}

export interface LoginResult {
  token: string
  id?: number
  userId?: number
  username: string
}
