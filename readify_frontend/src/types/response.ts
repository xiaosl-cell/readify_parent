// 通用返回结果接口
export interface ApiResponse<T> {
  code: string;      // 状态码
  message: string;   // 提示信息
  data: T;           // 返回数据
} 