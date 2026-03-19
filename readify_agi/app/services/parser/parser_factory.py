from app.core.config import settings
from app.services.parser.parser_service import ParserService


def get_parser_service() -> ParserService:
    provider = settings.PARSER_PROVIDER.strip().lower()
    if provider == "llama":
        from app.services.llama_parse_service import LlamaParseService
        return LlamaParseService()
    if provider == "tencent":
        from app.services.parser.tencent_ocr_parse_service import TencentOCRParseService
        return TencentOCRParseService()
    raise ValueError(f"不支持的 PARSER_PROVIDER: {provider}，可选值：tencent, llama")
