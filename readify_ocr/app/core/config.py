import os
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    OCR_HOST: str = os.getenv("OCR_HOST", "0.0.0.0")
    OCR_PORT: int = int(os.getenv("OCR_PORT", "8090"))

    OCR_DEVICE: str = os.getenv("OCR_DEVICE", "cpu")
    OCR_LANGUAGE: str = os.getenv("OCR_LANGUAGE", "ch")
    OCR_USE_DOC_ORIENTATION_CLASSIFY: bool = (
        os.getenv("OCR_USE_DOC_ORIENTATION_CLASSIFY", "false").lower() == "true"
    )
    OCR_USE_DOC_UNWARPING: bool = (
        os.getenv("OCR_USE_DOC_UNWARPING", "false").lower() == "true"
    )
    OCR_USE_TEXTLINE_ORIENTATION: bool = (
        os.getenv("OCR_USE_TEXTLINE_ORIENTATION", "false").lower() == "true"
    )

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()

