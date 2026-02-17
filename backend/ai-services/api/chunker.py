from fastapi import APIRouter, HTTPException
import time
import logging

from models.chunker_models import ChunkRequest, ChunkResponse, ChunkItem
from services.chunker import SemanticChunker, FixedSizeChunker, ChunkConfig, ChunkStrategy

router = APIRouter(prefix="/api/v1", tags=["chunker"])
logger = logging.getLogger(__name__)


@router.post("/chunk", response_model=ChunkResponse)
async def chunk_text(request: ChunkRequest):
    """对文本进行分块"""
    start_time = time.time()

    config = ChunkConfig(
        strategy=request.strategy,
        chunk_size=request.chunk_size or 512,
        overlap_rate=request.overlap_rate or 0.1
    )

    strategy = config.select_strategy(request.content, request.doc_type)

    if strategy == ChunkStrategy.SEMANTIC:
        chunker = SemanticChunker(
            min_chunk_size=config.min_chunk_size,
            max_chunk_size=config.max_chunk_size
        )
    else:
        chunker = FixedSizeChunker(
            chunk_size=config.chunk_size,
            overlap_rate=config.overlap_rate
        )

    chunks = chunker.chunk(request.content, request.doc_id)

    chunk_time = (time.time() - start_time) * 1000

    return ChunkResponse(
        chunks=[ChunkItem(
            chunk_id=c.chunk_id,
            content=c.content,
            position=c.position,
            metadata=c.metadata
        ) for c in chunks],
        total_chunks=len(chunks),
        strategy_used=strategy,
        chunk_time_ms=chunk_time
    )
