from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from services.chunker.chunk_config import ChunkStrategy


class ChunkRequest(BaseModel):
    content: str
    doc_id: str = ""
    doc_type: str = ""
    strategy: Optional[ChunkStrategy] = ChunkStrategy.AUTO
    chunk_size: Optional[int] = 512
    overlap_rate: Optional[float] = 0.1


class ChunkItem(BaseModel):
    chunk_id: str
    content: str
    position: int
    metadata: Dict[str, Any]


class ChunkResponse(BaseModel):
    chunks: List[ChunkItem]
    total_chunks: int
    strategy_used: ChunkStrategy
    chunk_time_ms: float
