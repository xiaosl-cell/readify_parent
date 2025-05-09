// 思维导图视图对象
export interface MindMapVO {
  id: number                // 思维导图ID
  projectId: number         // 工程ID
  fileId: number            // 文件ID
  title: string             // 思维导图标题
  type: string              // 笔记类型
  description: string       // 思维导图描述
  userId: number            // 用户ID
  createdAt: number         // 创建时间
  updatedAt: number         // 更新时间
}

// 创建思维导图请求参数
export interface CreateMindMapParams {
  projectId: number
  fileId: number
  title: string
  type: string
  description?: string
} 