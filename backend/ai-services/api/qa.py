from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
import time
import uuid
import logging
import asyncio

from models.qa_models import (
    ChatRequest, ChatResponse, ChatMessage, SourceReference, GraphContext
)
from services.qa import context_builder, sse_stream_handler, reference_annotator, qa_prompt_template
from services.search.rrf_fusion import rrf_fusion
from services.search.reranker import reranker_service
from services.embedding.milvus_client import milvus_client
from services.embedding.es_client import es_client
from services.embedding.qwen_embedding import qwen_embedding
from services.kg.graph.traversal_engine import traversal_engine
from services.kg.evidence.chain_builder import evidence_chain_builder
from config.settings import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/qa", tags=["问答服务"])


class SimpleChatRequest(BaseModel):
    query: str = Field(..., description="用户问题")
    stream: bool = Field(default=True, description="是否流式输出")
    top_k: int = Field(default=10, description="检索结果数量")


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    start_time = time.time()
    conversation_id = request.conversation_id or str(uuid.uuid4())
    
    logger.info(f"Chat request: query='{request.query[:50]}...', conv_id={conversation_id}")
    
    try:
        query_vector = await qwen_embedding.embed_single(request.query)
        
        keyword_results = es_client.search(
            query=request.query,
            top_k=request.keyword_top_k if hasattr(request, 'keyword_top_k') else 50,
            filters=request.filters
        )
        
        vector_results = milvus_client.search(
            query_vector=query_vector,
            top_k=request.vector_top_k if hasattr(request, 'vector_top_k') else 50
        )
        
        fused_results = rrf_fusion.fuse(keyword_results, vector_results)
        
        if request.use_rerank and len(fused_results) > 0:
            fused_results = await reranker_service.rerank(
                query=request.query,
                documents=fused_results,
                top_n=request.top_k
            )
        else:
            fused_results = fused_results[:request.top_k]
        
        graph_context = None
        if request.use_graph:
            try:
                graph_context = await _build_graph_context(request.query, fused_results)
            except Exception as e:
                logger.warning(f"Graph context build failed: {e}")
        
        context_result = context_builder.build_context(
            query=request.query,
            search_results=fused_results,
            graph_context=graph_context,
            history=[msg.model_dump() for msg in request.history] if request.history else None
        )
        
        answer = await sse_stream_handler.generate(
            query=request.query,
            context=context_result.context_text
        )
        
        annotated = reference_annotator.annotate_response(
            response=answer,
            sources=context_result.sources
        )
        
        sources = context_result.sources
        
        latency_ms = (time.time() - start_time) * 1000
        
        logger.info(f"Chat completed: {latency_ms:.1f}ms, {len(sources)} sources")
        
        return ChatResponse(
            answer=annotated.text,
            sources=sources,
            graph_context=graph_context,
            conversation_id=conversation_id,
            query=request.query,
            latency_ms=latency_ms
        )
        
    except Exception as e:
        logger.error(f"Chat error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/chat/stream")
async def chat_stream(request: ChatRequest):
    conversation_id = request.conversation_id or str(uuid.uuid4())
    
    logger.info(f"Stream chat request: query='{request.query[:50]}...'")
    
    async def generate():
        try:
            yield f"data: {{'type': 'start', 'conversation_id': '{conversation_id}'}}\n\n"
            
            query_vector = await qwen_embedding.embed_single(request.query)
            
            keyword_results = es_client.search(
                query=request.query,
                top_k=50,
                filters=request.filters
            )
            
            vector_results = milvus_client.search(
                query_vector=query_vector,
                top_k=50
            )
            
            fused_results = rrf_fusion.fuse(keyword_results, vector_results)
            
            if request.use_rerank and len(fused_results) > 0:
                fused_results = await reranker_service.rerank(
                    query=request.query,
                    documents=fused_results,
                    top_n=request.top_k
                )
            else:
                fused_results = fused_results[:request.top_k]
            
            graph_context = None
            if request.use_graph:
                try:
                    graph_context = await _build_graph_context(request.query, fused_results)
                except Exception as e:
                    logger.warning(f"Graph context build failed: {e}")
            
            context_result = context_builder.build_context(
                query=request.query,
                search_results=fused_results,
                graph_context=graph_context,
                history=[msg.model_dump() for msg in request.history] if request.history else None
            )
            
            async for chunk in sse_stream_handler.stream_generate(
                query=request.query,
                context=context_result.context_text,
                sources=context_result.sources
            ):
                yield chunk
            
        except Exception as e:
            logger.error(f"Stream error: {e}")
            yield f"data: {{'type': 'error', 'error': '{str(e)}'}}\n\n"
    
    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )


@router.post("/simple")
async def simple_chat(request: SimpleChatRequest):
    start_time = time.time()
    
    try:
        query_vector = await qwen_embedding.embed_single(request.query)
        
        keyword_results = es_client.search(query=request.query, top_k=30)
        vector_results = milvus_client.search(query_vector=query_vector, top_k=30)
        
        fused_results = rrf_fusion.fuse(keyword_results, vector_results)[:request.top_k]
        
        context_result = context_builder.build_context(
            query=request.query,
            search_results=fused_results
        )
        
        if request.stream:
            async def generate():
                async for chunk in sse_stream_handler.stream_generate(
                    query=request.query,
                    context=context_result.context_text,
                    sources=context_result.sources
                ):
                    yield chunk
            
            return StreamingResponse(
                generate(),
                media_type="text/event-stream"
            )
        else:
            answer = await sse_stream_handler.generate(
                query=request.query,
                context=context_result.context_text
            )
            
            latency_ms = (time.time() - start_time) * 1000
            
            return {
                "answer": answer,
                "sources": [s.model_dump() for s in context_result.sources],
                "latency_ms": latency_ms
            }
            
    except Exception as e:
        logger.error(f"Simple chat error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def qa_health():
    return {
        "status": "healthy",
        "services": {
            "embedding": "configured" if settings.QWEN_API_KEY else "not_configured",
            "milvus": "connected" if milvus_client._collection else "not_connected",
            "elasticsearch": "connected" if es_client.client else "not_connected"
        }
    }


async def _build_graph_context(
    query: str,
    search_results: List[Dict[str, Any]]
) -> Optional[GraphContext]:
    entities = []
    relations = []
    paths = []
    
    entity_keywords = _extract_keywords(query)
    
    for result in search_results[:5]:
        content = result.get("content", "")
        
        try:
            from services.kg.entity.llm_extractor import llm_entity_extractor
            extracted_entities = await llm_entity_extractor.extract(content[:500])
            
            for entity in extracted_entities[:3]:
                entities.append({
                    "name": entity.name,
                    "type": entity.type,
                    "description": entity.description
                })
        except Exception as e:
            logger.debug(f"Entity extraction skipped: {e}")
    
    return GraphContext(
        entities=entities[:10],
        relations=relations[:10],
        paths=paths[:3]
    )


def _extract_keywords(text: str) -> List[str]:
    import re
    words = re.findall(r'[\u4e00-\u9fa5]+|[a-zA-Z]+', text)
    return [w for w in words if len(w) >= 2][:5]
