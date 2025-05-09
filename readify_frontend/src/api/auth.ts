import request from '@/utils/request'

export interface LoginData {
  username: string
  password: string
}

export interface RegisterData extends LoginData {
  email: string
}

export const login = (data: LoginData) => {
  return request({
    url: '/auth/login',
    method: 'post',
    data
  })
}

export const register = (data: RegisterData) => {
  return request({
    url: '/auth/register',
    method: 'post',
    data
  })
} 