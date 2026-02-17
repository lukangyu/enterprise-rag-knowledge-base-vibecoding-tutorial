from pydantic import BaseModel, Field
from typing import Optional, Literal
from enum import Enum


class ChunkStrategy(str, Enum):
    SEMANTIC = "semantic"
    FIXED = "fixed"
    AUTO = "auto"


class ChunkConfig(BaseModel):
    strategy: ChunkStrategy = ChunkStrategy.AUTO
    chunk_size: int = Field(default=512, ge=100, le=2000)
    overlap_rate: float = Field(default=0.1, ge=0, le=0.5)
    min_chunk_size: int = Field(default=100, ge=50)
    max_chunk_size: int = Field(default=1000, ge=500)

    def select_strategy(self, content: str, doc_type: str = "") -> ChunkStrategy:
        """自动选择分块策略"""
        if self.strategy != ChunkStrategy.AUTO:
            return self.strategy

        if doc_type in ["pdf", "docx"]:
            return ChunkStrategy.SEMANTIC
        return ChunkStrategy.FIXED
