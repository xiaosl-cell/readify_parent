"""
Nacos service registration client.

Registers this service to Nacos on startup and deregisters on shutdown.
Only handles registration — no service discovery needed for readify_eval.
"""
import logging
import socket
from typing import Optional

try:
    from v2.nacos import (
        ClientConfig,
        DeregisterInstanceParam,
        NacosNamingService,
        RegisterInstanceParam,
    )
except Exception:  # pragma: no cover - nacos-sdk not installed
    ClientConfig = None  # type: ignore
    NacosNamingService = None  # type: ignore
    RegisterInstanceParam = None  # type: ignore
    DeregisterInstanceParam = None  # type: ignore

logger = logging.getLogger(__name__)


def _resolve_service_ip(configured_host: str) -> str:
    """Prefer configured host, otherwise try to detect a reachable local IP."""
    if configured_host:
        return configured_host
    try:
        return socket.gethostbyname(socket.gethostname())
    except Exception as exc:
        logger.warning("Failed to resolve service host (%s); fallback to 127.0.0.1", exc)
        return "127.0.0.1"


class NacosRegistry:
    def __init__(self, nacos_cfg, service_cfg) -> None:
        client_config = ClientConfig(
            server_addresses=nacos_cfg.server_addr,
            namespace_id=nacos_cfg.namespace,
            username=nacos_cfg.username,
            password=nacos_cfg.password,
        )
        self.client_config = client_config
        self.nacos_cfg = nacos_cfg
        self.service_name = service_cfg.name
        self.service_ip = _resolve_service_ip(service_cfg.host)
        self.service_port = service_cfg.port
        self.naming_service: Optional[NacosNamingService] = None

    async def start(self) -> None:
        self.naming_service = await NacosNamingService.create_naming_service(self.client_config)
        await self.naming_service.register_instance(
            RegisterInstanceParam(
                service_name=self.service_name,
                ip=self.service_ip,
                port=self.service_port,
                cluster_name=self.nacos_cfg.cluster,
                group_name=self.nacos_cfg.group,
                metadata={"preserved.register.source": "python"},
            )
        )
        logger.info(
            "Registered to Nacos service=%s group=%s namespace=%s ip=%s port=%s",
            self.service_name,
            self.nacos_cfg.group,
            self.nacos_cfg.namespace or "public",
            self.service_ip,
            self.service_port,
        )

    async def stop(self) -> None:
        if not self.naming_service:
            return
        await self.naming_service.deregister_instance(
            DeregisterInstanceParam(
                service_name=self.service_name,
                ip=self.service_ip,
                port=self.service_port,
                cluster_name=self.nacos_cfg.cluster,
                group_name=self.nacos_cfg.group,
            )
        )
        logger.info("Deregistered from Nacos service=%s", self.service_name)


registry: Optional[NacosRegistry] = None


async def start_nacos() -> None:
    """Register this service to Nacos if enabled."""
    from app.core.config import settings

    if not settings.nacos.enabled:
        logger.info("Nacos registration disabled; skip.")
        return

    if NacosNamingService is None:
        logger.error("nacos-sdk-python (v2) is not installed; unable to register service.")
        return

    global registry
    registry = NacosRegistry(settings.nacos, settings.service)
    try:
        await registry.start()
    except Exception as exc:
        logger.error("Nacos registration failed: %s", exc)
        registry = None


async def stop_nacos() -> None:
    """Deregister service on shutdown."""
    global registry
    if not registry:
        return
    try:
        await registry.stop()
    except Exception as exc:
        logger.error("Nacos deregistration failed: %s", exc)
    finally:
        registry = None
