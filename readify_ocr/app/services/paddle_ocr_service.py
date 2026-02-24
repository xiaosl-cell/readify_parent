import asyncio
import tempfile
from pathlib import Path
from typing import Any, List

from app.core.config import settings


def _to_jsonable(value: Any) -> Any:
    if value is None or isinstance(value, (str, int, float, bool)):
        return value

    if isinstance(value, dict):
        return {str(key): _to_jsonable(item) for key, item in value.items()}

    if isinstance(value, (list, tuple, set)):
        return [_to_jsonable(item) for item in value]

    if hasattr(value, "tolist"):
        try:
            return _to_jsonable(value.tolist())
        except Exception:
            pass

    if hasattr(value, "item"):
        try:
            return value.item()
        except Exception:
            pass

    return str(value)


def _normalize_line(line: Any) -> tuple[str, float | None]:
    if isinstance(line, str):
        return line.strip(), None
    if isinstance(line, dict):
        text = line.get("text")
        score = line.get("score")
        if isinstance(text, str):
            return text.strip(), float(score) if isinstance(score, (int, float)) else None
    if isinstance(line, (list, tuple)) and len(line) >= 2:
        candidate = line[1]
        if isinstance(candidate, (list, tuple)) and len(candidate) >= 1:
            text = candidate[0]
            score = candidate[1] if len(candidate) > 1 else None
            if isinstance(text, str):
                return text.strip(), float(score) if isinstance(score, (int, float)) else None
    return "", None


class PaddleOCRService:
    def __init__(self) -> None:
        from paddleocr import PaddleOCR

        self.ocr = PaddleOCR(
            lang=settings.OCR_LANGUAGE,
            use_doc_orientation_classify=settings.OCR_USE_DOC_ORIENTATION_CLASSIFY,
            use_doc_unwarping=settings.OCR_USE_DOC_UNWARPING,
            use_textline_orientation=settings.OCR_USE_TEXTLINE_ORIENTATION,
            device=settings.OCR_DEVICE,
        )

    def _predict(self, file_path: str) -> List[dict]:
        results = []
        for index, raw_result in enumerate(self.ocr.predict(file_path), start=1):
            rec_texts = raw_result.get("rec_texts") if isinstance(raw_result, dict) else None
            rec_scores = raw_result.get("rec_scores") if isinstance(raw_result, dict) else None

            lines = []
            if isinstance(rec_texts, list):
                for line_idx, text in enumerate(rec_texts):
                    if not isinstance(text, str):
                        continue
                    cleaned = text.strip()
                    if not cleaned:
                        continue
                    score_value = None
                    if isinstance(rec_scores, list) and line_idx < len(rec_scores):
                        score_raw = rec_scores[line_idx]
                        if isinstance(score_raw, (int, float)):
                            score_value = float(score_raw)
                    lines.append({"text": cleaned, "score": score_value})
            else:
                candidate_lines = raw_result.get("lines") if isinstance(raw_result, dict) else None
                if isinstance(candidate_lines, list):
                    for line in candidate_lines:
                        text, score = _normalize_line(line)
                        if not text:
                            continue
                        lines.append({"text": text, "score": score})

            page_text = "\n".join(line["text"] for line in lines if line.get("text"))
            results.append(
                {
                    "page": index,
                    "text": page_text,
                    "lines": lines,
                    "raw": _to_jsonable(raw_result) if isinstance(raw_result, dict) else None,
                }
            )
        return results

    async def parse_bytes(self, file_name: str, file_bytes: bytes) -> List[dict]:
        suffix = Path(file_name).suffix or ".bin"
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
            temp_file.write(file_bytes)
            temp_path = temp_file.name

        try:
            return await asyncio.to_thread(self._predict, temp_path)
        finally:
            temp = Path(temp_path)
            if temp.exists():
                temp.unlink()
