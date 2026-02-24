import base64

from fastapi import APIRouter, HTTPException

from app.schemas import OCRFileRequest, OCRFileResponse, OCRPage
from app.services.paddle_ocr_service import PaddleOCRService


router = APIRouter(prefix="/ocr", tags=["ocr"])
ocr_service = PaddleOCRService()


@router.get("/health")
async def health() -> dict:
    return {"status": "ok"}


@router.post("/file", response_model=OCRFileResponse)
async def ocr_file(request: OCRFileRequest) -> OCRFileResponse:
    try:
        file_bytes = base64.b64decode(request.content_base64)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Invalid content_base64: {exc}") from exc

    pages = await ocr_service.parse_bytes(request.filename, file_bytes)
    response_pages = [
        OCRPage(
            page=page.get("page", index + 1),
            text=page.get("text", ""),
            lines=page.get("lines", []),
            raw=page.get("raw"),
        )
        for index, page in enumerate(pages)
    ]
    return OCRFileResponse(pages=response_pages)

