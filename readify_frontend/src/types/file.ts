export interface FileVO {
  id: number
  originalName: string
  mimeType: string
  size: number
  createTime: number
  updateTime: number
}

export interface ResultListFileVO {
  code: string
  message: string
  data: FileVO[] | null
} 