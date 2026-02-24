from dataclasses import dataclass, field
from typing import Any, Dict, List, Protocol


@dataclass
class ParsedDocument:
    content: str
    metadata: Dict[str, Any] = field(default_factory=dict)

    def get_content(self) -> str:
        return self.content


class ParserService(Protocol):
    async def parse_file(self, file_path: str) -> List[ParsedDocument]:
        ...

