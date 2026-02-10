import api from './index'
import type { Result, LoginResult } from '@/types'

export const login = (username: string, password: string): Promise<Result<LoginResult>> => {
  return api.post('/auth/login', { username, password })
}

export const logout = (): void => {
  localStorage.removeItem('token')
}
