// 思维导图节点树形结构
export interface MindMapNodeTreeVO {
  id: number               // 节点ID
  projectId: number        // 项目ID
  fileId: number           // 文件ID
  mindMapId: number        // 思维导图ID
  parentId: number | null  // 父节点ID，根节点为null
  content: string          // 节点内容
  sequence: number         // 排序序号
  level: number            // 节点层级，根节点为0
  createdTime: number      // 创建时间
  updatedTime: number      // 更新时间
  children: MindMapNodeTreeVO[] // 子节点列表
} 