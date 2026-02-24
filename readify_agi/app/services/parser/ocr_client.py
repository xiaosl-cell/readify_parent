import base64
import asyncio
from pathlib import Path
from typing import Any, Dict, List

import httpx

from app.core.config import settings


class OCRClient:
    def __init__(self) -> None:
        self.base_url = settings.OCR_BASE_URL.rstrip("/")
        self.timeout = settings.OCR_TIMEOUT_SEC
        self.language = settings.OCR_LANG

    async def parse_file(self, file_path: str) -> List[Dict[str, Any]]:
        file_name = Path(file_path).name
        file_bytes = Path(file_path).read_bytes()
        payload = {
            "filename": file_name,
            "content_base64": base64.b64encode(file_bytes).decode("utf-8"),
            "language": self.language,
        }

        last_error: Exception | None = None
        for _ in range(3):
            try:
                async with httpx.AsyncClient(timeout=self.timeout, trust_env=False) as client:
                    response = await client.post(f"{self.base_url}/ocr/file", json=payload)
                    response.raise_for_status()
                break
            except Exception as exc:
                last_error = exc
                await asyncio.sleep(0.5)
        else:
            raise RuntimeError(f"OCR request failed: {last_error}")

        data = response.json()
        pages = data.get("pages") if isinstance(data, dict) else None
        if not isinstance(pages, list):
            return []
        return [page for page in pages if isinstance(page, dict)]
