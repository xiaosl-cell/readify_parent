from app.core.config import settings
from app.services.parser.local_parse_service import LocalParseService
from app.services.parser.parser_service import ParserService


def get_parser_service() -> ParserService:
    provider = settings.PARSER_PROVIDER.strip().lower()
    if provider == "llama":
        from app.services.llama_parse_service import LlamaParseService
        return LlamaParseService()
    return LocalParseService()
