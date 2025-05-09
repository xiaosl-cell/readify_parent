import axios from 'axios'
import { ElMessage } from 'element-plus'
import { getAuthHeader, removeToken } from './auth'
import type { ApiResponse } from '@/types/response'
import router from '@/router'
import store from '@/store'

const request = axios.create({
  baseURL: '/api',
  timeout: 10000
})

// 请求拦截器
request.interceptors.request.use(
  config => {
    const token = getAuthHeader()
    if (token) {
      config.headers.Authorization = token
    }
    return config
  },
  error => {
    return Promise.reject(error)
  }
)

// 响应拦截器
request.interceptors.response.use(
  response => {
    const res = response.data as ApiResponse
    
    if (res.code === '200') {
      return res
    }
    
    // 处理未认证或认证过期的情况
    if (res.code === '401' || res.code === '403') {
      ElMessage.error('登录已过期，请重新登录')
      // 清除用户状态
      store.dispatch('logout')
      removeToken()
      // 跳转到登录页
      router.push('/login')
      return Promise.reject(new Error('未认证'))
    }
    
    // 统一处理其他错误
    ElMessage.error(res.message || '请求失败')
    return Promise.reject(new Error(res.message || '请求失败'))
  },
  error => {
    // 处理网络错误等情况
    if (error.response) {
      const status = error.response.status
      if (status === 401 || status === 403) {
        ElMessage.error('登录已过期，请重新登录')
        store.dispatch('logout')
        removeToken()
        router.push('/login')
        return Promise.reject(new Error('未认证'))
      }
    }
    ElMessage.error(error.message || '请求失败')
    return Promise.reject(error)
  }
)

export default request 