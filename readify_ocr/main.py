import uvicorn
from fastapi import FastAPI

from app.api.ocr_router import router as ocr_router
from app.core.config import settings


app = FastAPI(title="readify-ocr", version="0.1.0")
app.include_router(ocr_router)


if __name__ == "__main__":
    uvicorn.run(app, host=settings.OCR_HOST, port=settings.OCR_PORT)

