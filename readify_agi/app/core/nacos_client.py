import asyncio
import logging
import socket
from typing import Optional

try:
    from v2.nacos import (
        NacosNamingService,
        ClientConfig,
        RegisterInstanceParam,
        DeregisterInstanceParam,
        NacosException,
    )
except Exception:  # pragma: no cover - optional dependency handled at runtime
    NacosNamingService = None  # type: ignore
    ClientConfig = None  # type: ignore
    RegisterInstanceParam = None  # type: ignore
    DeregisterInstanceParam = None  # type: ignore
    NacosException = Exception  # type: ignore

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
