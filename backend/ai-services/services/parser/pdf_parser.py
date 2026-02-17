import fitz
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import hashlib

logger = logging.getLogger(__name__)


@dataclass
class ParsedDocument:
    content: str
    metadata: Dict[str, Any]
    structure: List[Dict[str, Any]]
    page_count: int
    content_hash: str


class PDFParser:
    def __init__(self, chunk_size: int = 1000):
        self.chunk_size = chunk_size

    def parse(self, file_path: str) -> ParsedDocument:
        """解析PDF文件"""
        doc = fitz.open(file_path)
        return self._extract_content(doc)

    def _extract_content(self, doc) -> ParsedDocument:
        """提取PDF内容"""
        content_parts = []
        structure = []

        for page_num, page in enumerate(doc):
            text = page.get_text()
            content_parts.append(text)

            blocks = page.get_text("dict")["blocks"]
            for block in blocks:
                if "lines" in block:
                    for line in block["lines"]:
                        font_size = line["spans"][0]["size"] if line["spans"] else 0
                        if font_size > 12:
                            structure.append({
                                "type": "heading",
                                "text": line["spans"][0]["text"] if line["spans"] else "",
                                "page": page_num + 1,
                                "font_size": font_size
                            })

        content = "\n".join(content_parts)
        content_hash = hashlib.sha256(content.encode()).hexdigest()

        return ParsedDocument(
            content=content,
            metadata={
                "page_count": len(doc),
                "file_type": "pdf"
            },
            structure=structure,
            page_count=len(doc),
            content_hash=content_hash
        )

    def parse_stream(self, file_stream) -> ParsedDocument:
        """流式解析大文件"""
        doc = fitz.open(stream=file_stream.read(), filetype="pdf")
        return self._extract_content(doc)
