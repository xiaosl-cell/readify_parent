from sqlalchemy import Column, DateTime, BigInteger
from sqlalchemy.sql import func
from sqlalchemy.dialects.mysql import LONGTEXT

from app.core.database import Base


class AssistantThinkingDB(Base):
    __tablename__ = "assistant_thinking"

    id = Column(BigInteger, primary_key=True, autoincrement=True, comment="主键ID")
    project_id = Column(BigInteger, nullable=False, index=True, comment="工程ID")
    user_message_id = Column(BigInteger, nullable=False, index=True, comment="对应的用户消息ID")
    content = Column(LONGTEXT, nullable=False, comment="AI思考过程内容")
    created_at = Column(DateTime, nullable=False, server_default=func.now(), index=True, comment="创建时间")
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now(), comment="更新时间")

    def __repr__(self):
        return f"<AssistantThinking(id={self.id}, project_id={self.project_id}, user_message_id={self.user_message_id})" 