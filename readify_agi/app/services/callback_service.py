import aiohttp
import time
import traceback
from typing import Dict, Any, Optional
from app.core.config import settings

class CallbackService:
    """回调服务，用于通知第三方接口处理结果"""
    
    async def notify_file_processed(
        self, 
        file_id: int, 
        success: bool, 
        message: str = "",
        additional_data: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        通知第三方接口文件处理完成
        
        Args:
            file_id: 文件ID
            success: 处理是否成功
            message: 处理结果消息
            additional_data: 额外数据
            
        Returns:
            bool: 回调是否成功
        """
        # 获取回调配置
        callback_url = getattr(settings, "FILE_PROCESS_CALLBACK_URL", "")
        api_key = getattr(settings, "FILE_PROCESS_CALLBACK_API_KEY", "")
        
        if not callback_url:
            print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] 警告：未配置回调URL，跳过回调")
            return False
            
        if not api_key:
            print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] 警告：未配置回调API Key，跳过回调")
            return False
            
        # 准备回调数据
        payload = {
            "fileId": file_id,
            "success": success,
            "message": message,
            "timestamp": int(time.time())
        }
        
        # 添加额外数据
        if additional_data:
            payload.update(additional_data)
            
        # 准备请求头
        headers = {
            "Content-Type": "application/json",
            "X-API-Key": api_key
        }
            
        try:
            print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] 开始回调通知，URL: {callback_url}")
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    callback_url,
                    json=payload,
                    headers=headers,
                    timeout=10  # 10秒超时
                ) as response:
                    if response.status == 200:
                        response_text = await response.text()
                        print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] 回调成功，响应: {response_text}")
                        return True
                    else:
                        print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] 回调失败，状态码: {response.status}")
                        return False
        except Exception as e:
            print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] 回调异常: {str(e)}")
            print(traceback.format_exc())
            return False 