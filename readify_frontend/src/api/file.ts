import request from '@/utils/request'
import type { ResultListFileVO } from '@/types/file'

export const getProjectFiles = (projectId: number) => {
  return request<ResultListFileVO>({
    url: `/projects/${projectId}/files`,
    method: 'get'
  })
} 