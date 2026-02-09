"""
用户上下文模块

用于从请求头中提取用户信息，支持权限控制
"""
import logging
from dataclasses import dataclass
from typing import Optional

from fastapi import Request, Header

from app.services.vector_store_service import UserRole

logger = logging.getLogger(__name__)


@dataclass
class UserContext:
    """用户上下文信息"""
    user_id: Optional[int] = None
    user_role: str = UserRole.USER

    @property
    def is_admin(self) -> bool:
        return self.user_role == UserRole.ADMIN or self.user_role == "admin"

    @property
    def is_authenticated(self) -> bool:
        return self.user_id is not None and self.user_id > 0


def get_user_context(
    x_user_id: Optional[str] = Header(None, alias="X-User-Id"),
    x_user_role: Optional[str] = Header(None, alias="X-User-Role"),
) -> UserContext:
    """
    从请求头中提取用户上下文

    Headers:
        X-User-Id: 用户ID
        X-User-Role: 用户角色 (user/admin)

    Returns:
        UserContext: 用户上下文对象
    """
    logger.debug("Received headers: X-User-Id=%s, X-User-Role=%s", x_user_id, x_user_role)

    user_id = None
    if x_user_id:
        try:
            user_id = int(x_user_id)
        except (ValueError, TypeError):
            pass

    user_role = UserRole.USER
    if x_user_role and x_user_role.lower() in ["admin", "user"]:
        user_role = x_user_role.lower()

    ctx = UserContext(user_id=user_id, user_role=user_role)
    logger.info("UserContext created: user_id=%s, user_role=%s", ctx.user_id, ctx.user_role)
    return ctx
