import re
import logging
from typing import Dict, List, Any
from dataclasses import dataclass
import hashlib
import yaml

logger = logging.getLogger(__name__)


@dataclass
class ParsedDocument:
    content: str
    metadata: Dict[str, Any]
    structure: List[Dict[str, Any]]
    page_count: int
    content_hash: str


class MarkdownParser:
    def parse(self, content: str) -> ParsedDocument:
        """解析Markdown文档"""
        structure = []
        metadata = {"file_type": "markdown"}

        if content.startswith('---'):
            parts = content.split('---', 2)
            if len(parts) >= 3:
                try:
                    metadata.update(yaml.safe_load(parts[1]))
                    content = parts[2]
                except Exception:
                    pass

        heading_pattern = re.compile(r'^(#{1,6})\s+(.+)$', re.MULTILINE)
        for match in heading_pattern.finditer(content):
            level = len(match.group(1))
            text = match.group(2)
            structure.append({
                "type": "heading",
                "text": text,
                "level": level
            })

        content_hash = hashlib.sha256(content.encode()).hexdigest()

        return ParsedDocument(
            content=content,
            metadata=metadata,
            structure=structure,
            page_count=0,
            content_hash=content_hash
        )
