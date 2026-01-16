# 标准库导入
import logging
import time
import traceback
from typing import Any, Dict, Optional

# 第三方库导入
import aiohttp

# 本地应用导入
from app.core.config import settings
from app.core.nacos_client import get_service_discovery

logger = logging.getLogger(__name__)

class CallbackService:
    """回调服务，用于通知第三方接口处理结果"""
    
    async def _get_callback_url(self) -> Optional[str]:
        """
        通过Nacos服务发现获取回调URL
        
        Returns:
            回调URL，如果Nacos未启用或服务发现失败则返回None
        """
        if not settings.NACOS_ENABLED:
            logger.warning("Nacos未启用，无法获取回调URL")
            return None
        
        try:
            service_discovery = await get_service_discovery()
            if not service_discovery:
                logger.warning("无法创建Nacos服务发现客户端")
                return None
            
            # 从Nacos获取readify-server服务地址
            callback_url = await service_discovery.get_service_url(
                service_name=settings.READIFY_SERVER_SERVICE_NAME,
                path="/api/v1/files/vectorized",
                group_name=settings.NACOS_GROUP,
                use_https=False,
                strategy="random"
            )
            if callback_url:
                logger.debug(f"使用Nacos服务发现获取回调URL: {callback_url}")
                return callback_url
            else:
                logger.warning("Nacos服务发现未找到readify-server实例")
                return None
        except Exception as e:
            logger.error(f"Nacos服务发现失败: {e}")
            return None
    
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
        # 通过Nacos服务发现获取回调URL
        callback_url = await self._get_callback_url()
        api_key = getattr(settings, "FILE_PROCESS_CALLBACK_API_KEY", "")
        
        if not callback_url:
            error_msg = "无法通过Nacos服务发现获取回调URL"
            logger.error(error_msg)
            raise RuntimeError(error_msg)
            
        if not api_key:
            error_msg = "未配置回调API Key"
            logger.error(error_msg)
            raise ValueError(error_msg)
            
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
            logger.info(f"开始回调通知，URL: {callback_url}")
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    callback_url,
                    json=payload,
                    headers=headers,
                    timeout=10  # 10秒超时
                ) as response:
                    if response.status == 200:
                        response_text = await response.text()
                        logger.info(f"回调成功，响应: {response_text}")
                        return True
                    else:
                        logger.warning(f"回调失败，状态码: {response.status}")
                        return False
        except Exception as e:
            logger.error(f"回调异常: {str(e)}")
            logger.error(traceback.format_exc())
            return False 