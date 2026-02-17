import re
import logging
from typing import List, Dict, Any
from dataclasses import dataclass
import uuid

logger = logging.getLogger(__name__)


@dataclass
class Chunk:
    chunk_id: str
    content: str
    position: int
    metadata: Dict[str, Any]


class SemanticChunker:
    def __init__(self, min_chunk_size: int = 100, max_chunk_size: int = 1000):
        self.min_chunk_size = min_chunk_size
        self.max_chunk_size = max_chunk_size

    def chunk(self, text: str, doc_id: str = "") -> List[Chunk]:
        """基于语义边界进行分块"""
        chunks = []

        paragraphs = re.split(r'\n\s*\n', text)

        current_chunk = ""
        position = 0

        for para in paragraphs:
            para = para.strip()
            if not para:
                continue

            if len(current_chunk) + len(para) + 2 <= self.max_chunk_size:
                current_chunk = f"{current_chunk}\n\n{para}".strip()
            else:
                if current_chunk and len(current_chunk) >= self.min_chunk_size:
                    chunks.append(self._create_chunk(current_chunk, position, doc_id))
                    position += 1
                current_chunk = para

        if current_chunk and len(current_chunk) >= self.min_chunk_size:
            chunks.append(self._create_chunk(current_chunk, position, doc_id))

        return chunks

    def _create_chunk(self, content: str, position: int, doc_id: str) -> Chunk:
        return Chunk(
            chunk_id=str(uuid.uuid4()),
            content=content,
            position=position,
            metadata={
                "doc_id": doc_id,
                "char_count": len(content),
                "strategy": "semantic"
            }
        )
