import base64
import os
from pathlib import Path
from typing import List

import httpx

from app.services.parser.parser_service import ParsedDocument


class TencentOCRParseService:
    """浣跨敤鑵捐浜戦€氱敤鏂囧瓧璇嗗埆锛堥珮绮惧害鐗堬級瑙ｆ瀽鏂囦欢"""

    _API_URL = "https://ocr.tencentcloudapi.com/"
    _ACTION = "GeneralAccurateOCR"
    _VERSION = "2018-11-19"
    _REGION = "ap-guangzhou"

    def __init__(self) -> None:
        from app.core.config import settings
        self._secret_id = settings.TENCENT_SECRET_ID
        self._secret_key = settings.TENCENT_SECRET_KEY
        self._region = settings.TENCENT_OCR_REGION

    async def parse_file(self, file_path: str) -> List[ParsedDocument]:
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"鏂囦欢涓嶅瓨鍦? {file_path}")

        suffix = Path(file_path).suffix.lower()
        if suffix == ".pdf":
            return await self._parse_pdf(file_path)
        else:
            return await self._parse_image(file_path)

    async def _parse_pdf(self, file_path: str) -> List[ParsedDocument]:
        """璋冪敤鑵捐浜戦珮绮惧害鐗?OCR锛孭DF 閫愰〉澶勭悊"""
        try:
            import fitz  # pymupdf
        except ModuleNotFoundError as exc:
            raise RuntimeError(
                "PyMuPDF is required for PDF OCR parsing. Install dependency 'PyMuPDF'."
            ) from exc

        doc = fitz.open(file_path)
        documents: List[ParsedDocument] = []
        for page_num in range(len(doc)):
            page = doc[page_num]
            pix = page.get_pixmap(dpi=150)
            img_bytes = pix.tobytes("png")
            text = await self._call_ocr_image_bytes(img_bytes)
            if text.strip():
                documents.append(ParsedDocument(
                    content=text,
                    metadata={"page": page_num + 1, "source": file_path},
                ))
        doc.close()
        return documents

    async def _parse_image(self, file_path: str) -> List[ParsedDocument]:
        img_bytes = Path(file_path).read_bytes()
        text = await self._call_ocr_image_bytes(img_bytes)
        if not text.strip():
            return []
        return [ParsedDocument(
            content=text,
            metadata={"page": 1, "source": file_path},
        )]

    async def _call_ocr_image_bytes(self, img_bytes: bytes) -> str:
        import hashlib
        import hmac
        import json
        import time

        img_b64 = base64.b64encode(img_bytes).decode("utf-8")
        payload = {"ImageBase64": img_b64}
        payload_str = json.dumps(payload)

        timestamp = int(time.time())
        date = __import__("datetime").datetime.utcfromtimestamp(timestamp).strftime("%Y-%m-%d")

        # 鑵捐浜戠鍚?v3
        canonical_headers = "content-type:application/json\nhost:ocr.tencentcloudapi.com\n"
        signed_headers = "content-type;host"
        hashed_payload = hashlib.sha256(payload_str.encode("utf-8")).hexdigest()
        canonical_request = "\n".join([
            "POST", "/", "",
            canonical_headers, signed_headers, hashed_payload,
        ])

        credential_scope = f"{date}/ocr/tc3_request"
        string_to_sign = "\n".join([
            "TC3-HMAC-SHA256",
            str(timestamp),
            credential_scope,
            hashlib.sha256(canonical_request.encode("utf-8")).hexdigest(),
        ])

        def _sign(key: bytes, msg: str) -> bytes:
            return hmac.new(key, msg.encode("utf-8"), hashlib.sha256).digest()  # type: ignore[attr-defined]

        secret_date = _sign(f"TC3{self._secret_key}".encode("utf-8"), date)
        secret_service = _sign(secret_date, "ocr")
        secret_signing = _sign(secret_service, "tc3_request")
        signature = hmac.new(secret_signing, string_to_sign.encode("utf-8"), hashlib.sha256).hexdigest()

        authorization = (
            f"TC3-HMAC-SHA256 Credential={self._secret_id}/{credential_scope}, "
            f"SignedHeaders={signed_headers}, Signature={signature}"
        )

        headers = {
            "Authorization": authorization,
            "Content-Type": "application/json",
            "Host": "ocr.tencentcloudapi.com",
            "X-TC-Action": self._ACTION,
            "X-TC-Version": self._VERSION,
            "X-TC-Timestamp": str(timestamp),
            "X-TC-Region": self._region,
        }

        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.post(self._API_URL, headers=headers, content=payload_str)
            response.raise_for_status()

        data = response.json()
        error = data.get("Response", {}).get("Error")
        if error:
            raise RuntimeError(f"鑵捐浜?OCR 閿欒: {error.get('Code')} - {error.get('Message')}")

        text_detections = data.get("Response", {}).get("TextDetections", [])
        lines = [item.get("DetectedText", "") for item in text_detections]
        return "\n".join(lines)
