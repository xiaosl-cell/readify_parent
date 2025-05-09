from sqlalchemy import Column, Integer, Boolean, DateTime, Enum, BigInteger
from sqlalchemy.dialects.mysql import LONGTEXT
from sqlalchemy.sql import func

from app.core.database import Base


class ConversationHistoryDB(Base):
    __tablename__ = "conversation_history"

    id = Column(BigInteger, primary_key=True, autoincrement=True, comment="主键ID")
    project_id = Column(BigInteger, nullable=False, index=True, comment="工程ID")
    message_type = Column(
        Enum('system', 'user', 'assistant'),
        nullable=False,
        index=True,
        comment="消息类型：系统消息/用户问题/助手消息"
    )
    content = Column(LONGTEXT, nullable=False, comment="消息内容")
    priority = Column(Integer, nullable=False, default=1, comment="优先级：数值越大优先级越高，裁剪时优先保留")
    is_included_in_context = Column(Boolean, nullable=False, default=True, comment="是否包含在上下文中：0-不包含，1-包含")
    sequence = Column(Integer, nullable=False, default=0, index=True, comment="对话序号，同一会话中的排序")
    created_at = Column(DateTime, nullable=False, server_default=func.now(), index=True, comment="创建时间")
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now(), comment="更新时间")

    def __repr__(self):
        return f"<ConversationHistory(id={self.id}, project_id={self.project_id}, message_type={self.message_type}, sequence={self.sequence})>" 