from pydantic import BaseModel, Field
from typing import List, Optional


class EmbedRequest(BaseModel):
    texts: List[str]
    doc_id: str = ""
    chunk_ids: Optional[List[str]] = None


class EmbedResponse(BaseModel):
    vector_ids: List[str]
    dimension: int
    embed_time_ms: float


class SearchRequest(BaseModel):
    query: str
    top_k: int = Field(default=10, ge=1, le=100)
    doc_ids: Optional[List[str]] = None


class SearchResult(BaseModel):
    id: str
    score: float
    doc_id: str
    chunk_id: str
    content: str


class SearchResponse(BaseModel):
    results: List[SearchResult]
    search_time_ms: float


class DeleteRequest(BaseModel):
    doc_id: str
