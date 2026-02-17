from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
import asyncio
import time
import logging

from services.embedding.es_client import es_client
from services.embedding.milvus_client import milvus_client
from services.search.rrf_fusion import rrf_fusion
from config.settings import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/search", tags=["混合检索"])


class HybridSearchRequest(BaseModel):
    query: str = Field(..., description="查询文本")
    top_k: int = Field(default=20, description="返回结果数量")
    keyword_enabled: bool = Field(default=True, description="是否启用关键词检索")
    vector_enabled: bool = Field(default=True, description="是否启用向量检索")
    filters: Optional[Dict[str, Any]] = Field(default=None, description="过滤条件")
    keyword_top_k: int = Field(default=100, description="关键词检索返回数量")
    vector_top_k: int = Field(default=100, description="向量检索返回数量")
    rrf_k: int = Field(default=60, description="RRF融合参数k")


class SearchResult(BaseModel):
    doc_id: str
    chunk_id: Optional[str] = None
    content: Optional[str] = None
    score: float
    rank: int
    source: str
    metadata: Optional[Dict[str, Any]] = None


class HybridSearchResponse(BaseModel):
    results: List[Dict[str, Any]]
    keyword_time_ms: float
    vector_time_ms: float
    fusion_time_ms: float
    total_time_ms: float
    keyword_result_count: int
    vector_result_count: int
    final_result_count: int


@router.post("/hybrid", response_model=HybridSearchResponse)
async def hybrid_search(request: HybridSearchRequest):
    start_time = time.time()
    
    keyword_results = []
    vector_results = []
    keyword_time_ms = 0
    vector_time_ms = 0

    async def run_keyword_search():
        nonlocal keyword_results, keyword_time_ms
        if not request.keyword_enabled:
            return
        try:
            kw_start = time.time()
            keyword_results = es_client.search(
                query=request.query,
                top_k=request.keyword_top_k,
                filters=request.filters
            )
            keyword_time_ms = (time.time() - kw_start) * 1000
        except Exception as e:
            logger.error(f"Keyword search failed: {e}")

    async def run_vector_search():
        nonlocal vector_results, vector_time_ms
        if not request.vector_enabled:
            return
        try:
            vec_start = time.time()
            from services.embedding.qwen_embedding import qwen_embedding
            query_vector = await qwen_embedding.embed_single(request.query)
            vector_results = milvus_client.search(
                query_vector=query_vector,
                top_k=request.vector_top_k
            )
            vector_time_ms = (time.time() - vec_start) * 1000
        except Exception as e:
            logger.error(f"Vector search failed: {e}")

    await asyncio.gather(run_keyword_search(), run_vector_search())

    fusion_start = time.time()
    fused_results = rrf_fusion.fuse(
        keyword_results=keyword_results,
        vector_results=vector_results,
        k=request.rrf_k
    )
    fusion_time_ms = (time.time() - fusion_start) * 1000

    if len(fused_results) > request.top_k:
        fused_results = fused_results[:request.top_k]

    total_time_ms = (time.time() - start_time) * 1000

    logger.info(
        f"Hybrid search completed: keyword={len(keyword_results)} ({keyword_time_ms:.1f}ms), "
        f"vector={len(vector_results)} ({vector_time_ms:.1f}ms), "
        f"fusion={len(fused_results)} ({fusion_time_ms:.1f}ms), "
        f"total={total_time_ms:.1f}ms"
    )

    return HybridSearchResponse(
        results=fused_results,
        keyword_time_ms=keyword_time_ms,
        vector_time_ms=vector_time_ms,
        fusion_time_ms=fusion_time_ms,
        total_time_ms=total_time_ms,
        keyword_result_count=len(keyword_results),
        vector_result_count=len(vector_results),
        final_result_count=len(fused_results)
    )


@router.get("/keyword")
async def keyword_search(
    query: str = Query(..., description="查询文本"),
    top_k: int = Query(default=20, description="返回结果数量")
):
    start_time = time.time()
    
    try:
        results = es_client.search(query=query, top_k=top_k)
        time_ms = (time.time() - start_time) * 1000
        
        logger.info(f"Keyword search: query='{query[:50]}...', {len(results)} results in {time_ms:.1f}ms")
        
        return {
            "results": results,
            "time_ms": time_ms,
            "count": len(results)
        }
    except Exception as e:
        logger.error(f"Keyword search failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/vector")
async def vector_search(
    query: str = Query(..., description="查询文本"),
    top_k: int = Query(default=20, description="返回结果数量")
):
    start_time = time.time()
    
    try:
        from services.embedding.qwen_embedding import qwen_embedding
        query_vector = await qwen_embedding.embed_single(query)
        
        results = milvus_client.search(query_vector=query_vector, top_k=top_k)
        time_ms = (time.time() - start_time) * 1000
        
        logger.info(f"Vector search: {len(results)} results in {time_ms:.1f}ms")
        
        return {
            "results": results,
            "time_ms": time_ms,
            "count": len(results)
        }
    except Exception as e:
        logger.error(f"Vector search failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def health_check():
    es_health = es_client.health_check()
    milvus_health = milvus_client.health_check()
    
    return {
        "elasticsearch": {
            "status": es_health.get("status", "unknown"),
            "cluster_name": es_health.get("cluster_name", "")
        },
        "milvus": {
            "status": "healthy" if milvus_health else "unhealthy"
        }
    }
