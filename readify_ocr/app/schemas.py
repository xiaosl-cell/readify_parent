from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class OCRFileRequest(BaseModel):
    filename: str = Field(..., description="Original file name")
    content_base64: str = Field(..., description="Base64 encoded file bytes")
    language: Optional[str] = Field(default=None, description="OCR language code")


class OCRLine(BaseModel):
    text: str
    score: Optional[float] = None


class OCRPage(BaseModel):
    page: int
    text: str
    lines: List[OCRLine]
    raw: Optional[Dict[str, Any]] = None


class OCRFileResponse(BaseModel):
    pages: List[OCRPage]

