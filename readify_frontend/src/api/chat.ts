import request from '@/utils/request'

// 发送聊天消息
export function sendChatMessage(data: { query: string; projectId: number }) {
  return request({
    url: '/chat/message',
    method: 'post',
    data
  })
}

// 获取聊天历史 (旧方法，保留以兼容现有代码)
export function getChatHistory(projectId: number) {
  return request({
    url: `/chat/history/${projectId}`,
    method: 'get'
  })
}

// 获取项目对话记录，按照新API规范
export function getProjectConversations(projectId: number) {
  return request({
    url: `/conversation/project/${projectId}`,
    method: 'get'
  })
} 