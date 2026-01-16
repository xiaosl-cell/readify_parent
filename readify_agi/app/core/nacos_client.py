import asyncio
import logging
import socket
import random
from typing import Optional, List, Dict, Any

try:
    from v2.nacos import (
        NacosNamingService,
        ClientConfig,
        RegisterInstanceParam,
        DeregisterInstanceParam,
        NacosException,
    )
    # ListInstanceParam 用于服务发现
    try:  # pragma: no cover
        from v2.nacos.naming.model.naming_param import ListInstanceParam  # type: ignore
    except Exception:  # pragma: no cover
        ListInstanceParam = None  # type: ignore
except Exception:  # pragma: no cover - optional dependency handled at runtime
    NacosNamingService = None  # type: ignore
    ClientConfig = None  # type: ignore
    RegisterInstanceParam = None  # type: ignore
    DeregisterInstanceParam = None  # type: ignore
    NacosException = Exception  # type: ignore
    ListInstanceParam = None  # type: ignore
    SelectInstanceParam = None  # type: ignore

from app.core.config import settings

logger = logging.getLogger(__name__)


def _resolve_service_ip() -> str:
    """Prefer configured host, otherwise try to detect a reachable local IP."""
    if settings.SERVICE_HOST:
        return settings.SERVICE_HOST
    try:
        return socket.gethostbyname(socket.gethostname())
    except Exception as exc:  # pragma: no cover - best effort fallback
        logger.warning("Failed to resolve service host (%s); fallback to 127.0.0.1", exc)
        return "127.0.0.1"


class NacosRegistry:
    def __init__(self) -> None:
        client_config = ClientConfig(
            server_addresses=settings.NACOS_SERVER_ADDR,
            namespace_id=settings.NACOS_NAMESPACE,
            username=settings.NACOS_USERNAME,
            password=settings.NACOS_PASSWORD,
        )
        self.client_config = client_config
        self.service_ip = _resolve_service_ip()
        self.service_port = settings.SERVICE_PORT
        self.naming_service: Optional[NacosNamingService] = None

    async def start(self) -> None:
        self.naming_service = await NacosNamingService.create_naming_service(self.client_config)
        await self.naming_service.register_instance(
            RegisterInstanceParam(
                service_name=settings.SERVICE_NAME,
                ip=self.service_ip,
                port=self.service_port,
                cluster_name=settings.NACOS_CLUSTER,
                group_name=settings.NACOS_GROUP,
                metadata={"preserved.register.source": "python"},
            )
        )
        logger.info(
            "Registered to Nacos service=%s group=%s namespace=%s ip=%s port=%s",
            settings.SERVICE_NAME,
            settings.NACOS_GROUP,
            settings.NACOS_NAMESPACE or "public",
            self.service_ip,
            self.service_port,
        )

    async def stop(self) -> None:
        if not self.naming_service:
            return
        await self.naming_service.deregister_instance(
            DeregisterInstanceParam(
                service_name=settings.SERVICE_NAME,
                ip=self.service_ip,
                port=self.service_port,
                cluster_name=settings.NACOS_CLUSTER,
                group_name=settings.NACOS_GROUP,
            )
        )
        logger.info("Deregistered from Nacos service=%s", settings.SERVICE_NAME)


registry: Optional[NacosRegistry] = None


async def start_nacos() -> None:
    """Register this service to Nacos if enabled."""
    if not settings.NACOS_ENABLED:
        logger.info("Nacos registration disabled; skip.")
        return

    if NacosNamingService is None:
        logger.error("nacos-sdk-python (v2) is not installed; unable to register service.")
        return

    global registry
    registry = NacosRegistry()
    try:
        await registry.start()
    except Exception as exc:  # pragma: no cover - startup failures reported
        logger.error("Nacos registration failed: %s", exc)
        registry = None


async def stop_nacos() -> None:
    """Deregister service and stop heartbeat."""
    global registry
    if not registry:
        return
    try:
        await registry.stop()
    except Exception as exc:  # pragma: no cover
        logger.error("Nacos deregistration failed: %s", exc)
    finally:
        registry = None


class NacosServiceDiscovery:
    """Nacos服务发现客户端，用于发现和调用其他服务"""
    
    def __init__(self) -> None:
        client_config = ClientConfig(
            server_addresses=settings.NACOS_SERVER_ADDR,
            namespace_id=settings.NACOS_NAMESPACE,
            username=settings.NACOS_USERNAME,
            password=settings.NACOS_PASSWORD,
        )
        self.client_config = client_config
        self.naming_service: Optional[NacosNamingService] = None
        self._instance_cache: Dict[str, List[Dict[str, Any]]] = {}
        self._cache_lock = asyncio.Lock()
    
    async def _get_naming_service(self) -> Optional[NacosNamingService]:
        """获取或创建Nacos命名服务实例"""
        if self.naming_service is None:
            if NacosNamingService is None:
                logger.error("nacos-sdk-python (v2) is not installed; unable to discover services.")
                return None
            try:
                self.naming_service = await NacosNamingService.create_naming_service(self.client_config)
            except Exception as exc:
                logger.error("Failed to create Nacos naming service: %s", exc)
                return None
        return self.naming_service
    
    async def get_service_instances(
        self, 
        service_name: str, 
        group_name: Optional[str] = None,
        healthy_only: bool = True
    ) -> List[Dict[str, Any]]:
        """
        获取服务的所有实例
        
        Args:
            service_name: 服务名称
            group_name: 服务组名，默认使用配置的NACOS_GROUP
            healthy_only: 是否只返回健康的实例
        
        Returns:
            服务实例列表，每个实例包含ip、port等信息
        """
        if not settings.NACOS_ENABLED:
            logger.warning("Nacos is disabled, cannot discover service: %s", service_name)
            return []
        
        naming_service = await self._get_naming_service()
        if not naming_service:
            return []
        
        group = group_name or settings.NACOS_GROUP
        
        try:
            # 查询服务实例
            # nacos-sdk-python v2 API 使用 list_instances 方法
            instances = None
            if ListInstanceParam:
                try:
                    param = ListInstanceParam(
                        service_name=service_name,
                        group_name=group,
                        healthy_only=healthy_only,
                    )
                    instances = await naming_service.list_instances(param)
                except Exception as e:
                    logger.debug(f"ListInstanceParam方式失败: {e}，尝试其他方式")
            
            # 如果ListInstanceParam方式失败，尝试直接传递参数
            if instances is None:
                try:
                    # 直接传递参数的方式（如果API支持）
                    instances = await naming_service.list_instances(
                        service_name=service_name,
                        group_name=group,
                        healthy_only=healthy_only,
                    )
                except (TypeError, AttributeError) as e:
                    logger.warning(f"无法使用list_instances方法: {e}")
                    return []
            
            if not instances:
                logger.warning(f"服务 {service_name} 未找到可用实例")
                return []
            
            instance_list = []
            for instance in instances:
                # 处理不同的实例对象格式
                if hasattr(instance, 'ip'):
                    ip = instance.ip
                    port = instance.port
                    healthy = getattr(instance, 'healthy', True)
                    metadata = getattr(instance, 'metadata', {})
                elif isinstance(instance, dict):
                    ip = instance.get('ip', '')
                    port = instance.get('port', 0)
                    healthy = instance.get('healthy', True)
                    metadata = instance.get('metadata', {})
                else:
                    logger.warning(f"未知的实例格式: {type(instance)}")
                    continue
                
                instance_list.append({
                    "ip": ip,
                    "port": port,
                    "healthy": healthy,
                    "metadata": metadata,
                })
            
            # 更新缓存
            async with self._cache_lock:
                self._instance_cache[service_name] = instance_list
            
            logger.debug(
                "Discovered %d instances for service %s (group=%s, healthy_only=%s)",
                len(instance_list),
                service_name,
                group,
                healthy_only
            )
            return instance_list
            
        except Exception as exc:
            logger.error("Failed to discover service %s: %s", service_name, exc)
            # 返回缓存中的实例（如果有）
            async with self._cache_lock:
                return self._instance_cache.get(service_name, [])
    
    async def select_one_instance(
        self,
        service_name: str,
        group_name: Optional[str] = None,
        healthy_only: bool = True,
        strategy: str = "random"
    ) -> Optional[Dict[str, Any]]:
        """
        选择一个服务实例（负载均衡）
        
        Args:
            service_name: 服务名称
            group_name: 服务组名
            healthy_only: 是否只选择健康的实例
            strategy: 负载均衡策略，支持 "random"（随机）或 "round_robin"（轮询）
        
        Returns:
            选中的服务实例，包含ip和port，如果未找到则返回None
        """
        instances = await self.get_service_instances(service_name, group_name, healthy_only)
        if not instances:
            logger.warning("No instances found for service: %s", service_name)
            return None
        
        if strategy == "random":
            return random.choice(instances)
        elif strategy == "round_robin":
            # 简单的轮询实现（可以改进为使用全局计数器）
            return instances[0]
        else:
            logger.warning("Unknown load balancing strategy: %s, using random", strategy)
            return random.choice(instances)
    
    async def get_service_url(
        self,
        service_name: str,
        path: str = "",
        group_name: Optional[str] = None,
        use_https: bool = False,
        strategy: str = "random"
    ) -> Optional[str]:
        """
        获取服务的完整URL
        
        Args:
            service_name: 服务名称
            path: 路径（如 "/api/v1/files"）
            group_name: 服务组名
            use_https: 是否使用HTTPS
            strategy: 负载均衡策略
        
        Returns:
            完整的服务URL，如果未找到实例则返回None
        """
        instance = await self.select_one_instance(service_name, group_name, strategy=strategy)
        if not instance:
            return None
        
        protocol = "https" if use_https else "http"
        url = f"{protocol}://{instance['ip']}:{instance['port']}"
        if path:
            if not path.startswith("/"):
                path = "/" + path
            url += path
        
        return url


# 全局服务发现实例
_service_discovery: Optional[NacosServiceDiscovery] = None


async def get_service_discovery() -> Optional[NacosServiceDiscovery]:
    """获取全局服务发现实例"""
    global _service_discovery
    if _service_discovery is None:
        if not settings.NACOS_ENABLED:
            logger.warning("Nacos is disabled, service discovery unavailable")
            return None
        _service_discovery = NacosServiceDiscovery()
    return _service_discovery
