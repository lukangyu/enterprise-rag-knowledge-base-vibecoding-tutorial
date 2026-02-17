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


class FixedSizeChunker:
    def __init__(self, chunk_size: int = 512, overlap_rate: float = 0.1):
        self.chunk_size = chunk_size
        self.overlap = int(chunk_size * overlap_rate)

    def chunk(self, text: str, doc_id: str = "") -> List[Chunk]:
        """按固定大小进行分块，支持重叠"""
        chunks = []
        position = 0
        start = 0

        while start < len(text):
            end = start + self.chunk_size

            if end < len(text):
                for i in range(end, min(end + 50, len(text))):
                    if text[i] in '.!?。！？':
                        end = i + 1
                        break

            chunk_content = text[start:end].strip()

            if chunk_content:
                chunks.append(Chunk(
                    chunk_id=str(uuid.uuid4()),
                    content=chunk_content,
                    position=position,
                    metadata={
                        "doc_id": doc_id,
                        "char_count": len(chunk_content),
                        "start_offset": start,
                        "end_offset": end,
                        "strategy": "fixed"
                    }
                ))
                position += 1

            start = end - self.overlap

        return chunks
