import asyncio
import os
import shutil
import tempfile
from pathlib import Path
from urllib.parse import urlparse

from minio import Minio

from app.core.config import settings


class ObjectStorageService:
    def __init__(self) -> None:
        endpoint, secure = self._normalize_endpoint(settings.MINIO_ENDPOINT, settings.MINIO_SECURE)
        self.client = Minio(
            endpoint=endpoint,
            access_key=settings.MINIO_ACCESS_KEY,
            secret_key=settings.MINIO_SECRET_KEY,
            secure=secure,
        )

    @staticmethod
    def _normalize_endpoint(endpoint: str, secure: bool) -> tuple[str, bool]:
        if not endpoint:
            raise ValueError("MINIO_ENDPOINT is required for object storage access")
        parsed = urlparse(endpoint)
        if parsed.scheme in ("http", "https"):
            return parsed.netloc or parsed.path, secure or parsed.scheme == "https"
        return endpoint, secure

    def _download_to_temp(self, bucket: str, storage_key: str) -> str:
        response = self.client.get_object(bucket, storage_key)
        try:
            suffix = Path(storage_key).suffix
            fd, temp_path = tempfile.mkstemp(prefix="readify_", suffix=suffix)
            with os.fdopen(fd, "wb") as output:
                shutil.copyfileobj(response, output)
            return temp_path
        finally:
            response.close()
            response.release_conn()

    async def download_to_temp(self, bucket: str, storage_key: str) -> str:
        return await asyncio.to_thread(self._download_to_temp, bucket, storage_key)
