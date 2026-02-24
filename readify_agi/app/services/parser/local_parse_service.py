import os
from typing import List

from app.services.parser.ocr_client import OCRClient
from app.services.parser.parser_service import ParsedDocument


class LocalParseService:
    def __init__(self) -> None:
        self.ocr_client = OCRClient()

    async def parse_file(self, file_path: str) -> List[ParsedDocument]:
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"文件不存在: {file_path}")

        pages = await self.ocr_client.parse_file(file_path)
        documents: List[ParsedDocument] = []

        for index, page in enumerate(pages):
            text = self._extract_page_text(page)
            if not text:
                continue
            metadata = {
                "page": page.get("page") or page.get("page_index") or index + 1,
                "source": "ocr",
            }
            documents.append(ParsedDocument(content=text, metadata=metadata))

        if not documents:
            raise ValueError(f"文件解析失败，OCR未提取到文本: {file_path}")

        return documents

    @staticmethod
    def _extract_page_text(page: dict) -> str:
        for key in ("text", "content", "markdown"):
            value = page.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip()

        lines = page.get("lines")
        if isinstance(lines, list):
            normalized_lines = []
            for line in lines:
                if isinstance(line, str):
                    normalized_lines.append(line.strip())
                elif isinstance(line, dict):
                    raw_text = line.get("text") or line.get("content")
                    if isinstance(raw_text, str):
                        normalized_lines.append(raw_text.strip())
            merged_text = "\n".join(item for item in normalized_lines if item)
            if merged_text.strip():
                return merged_text.strip()

        return ""

