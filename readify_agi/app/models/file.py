from sqlalchemy import Column, BigInteger, String, Boolean
from pydantic import BaseModel, ConfigDict
from typing import Optional
from app.core.database import Base


class FileDB(Base):
    """File database model."""
    __tablename__ = "file"

    id = Column(BigInteger, primary_key=True, autoincrement=True, comment="Primary key")
    original_name = Column(String(255), nullable=False, comment="Original filename")
    storage_key = Column(String(255), nullable=False, comment="Object storage key")
    storage_bucket = Column(String(100), nullable=False, comment="Object storage bucket")
    storage_type = Column(String(20), nullable=False, default="minio", comment="Storage type")
    size = Column(BigInteger, nullable=False, comment="File size in bytes")
    mime_type = Column(String(100), comment="MIME type")
    md5 = Column(String(32), comment="File MD5")
    create_time = Column(BigInteger, nullable=False, comment="Create time")
    update_time = Column(BigInteger, nullable=False, comment="Update time")
    deleted = Column(Boolean, nullable=False, default=False, comment="Deleted")
    vectorized = Column(Boolean, nullable=False, default=False, comment="Vectorized")


class FileBase(BaseModel):
    """File base model."""
    model_config = ConfigDict(from_attributes=True)

    original_name: str
    storage_key: str
    storage_bucket: str
    storage_type: str
    size: int
    mime_type: Optional[str] = None
    md5: Optional[str] = None


class FileCreate(FileBase):
    """File create model."""
    pass


class FileResponse(FileBase):
    """File response model."""
    id: int
    create_time: int
    update_time: int
    deleted: bool = False
    vectorized: bool = False
