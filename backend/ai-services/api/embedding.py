from fastapi import APIRouter, HTTPException
import time
import logging

from models.embedding_models import (
    EmbedRequest, EmbedResponse,
    SearchRequest, SearchResponse, SearchResult,
    DeleteRequest
)
from services.embedding import QwenEmbedding, milvus_client
from services.embedding.es_client import es_client
from config.dependencies import get_milvus_connection

router = APIRouter(prefix="/api/v1", tags=["embedding"])
logger = logging.getLogger(__name__)


@router.post("/embed", response_model=EmbedResponse)
async def embed_texts(request: EmbedRequest):
    start_time = time.time()

    embedding_service = QwenEmbedding()
    embeddings = await embedding_service.embed_batch(request.texts)

    chunk_ids = request.chunk_ids or [str(i) for i in range(len(request.texts))]
    
    vectors = [
        {
            "doc_id": request.doc_id,
            "chunk_id": chunk_ids[i],
            "content": request.texts[i],
            "embedding": embeddings[i]
        }
        for i in range(len(request.texts))
    ]

    vector_ids = milvus_client.insert(vectors)

    es_documents = [
        {
            "doc_id": request.doc_id,
            "chunk_id": chunk_ids[i],
            "content": request.texts[i],
            "title": request.title,
            "keywords": request.keywords,
            "metadata": request.metadata,
            "milvus_id": vector_ids[i] if i < len(vector_ids) else ""
        }
        for i in range(len(request.texts))
    ]
    
    try:
        es_client.bulk_index(es_documents)
        logger.info(f"Indexed {len(es_documents)} documents in Elasticsearch")
    except Exception as e:
        logger.warning(f"Failed to index in Elasticsearch: {e}")

    embed_time = (time.time() - start_time) * 1000

    return EmbedResponse(
        vector_ids=vector_ids,
        dimension=len(embeddings[0]) if embeddings else 0,
        embed_time_ms=embed_time
    )


@router.post("/embed/dual")
async def embed_dual_storage(request: EmbedRequest):
    start_time = time.time()

    embedding_service = QwenEmbedding()
    embeddings = await embedding_service.embed_batch(request.texts)

    chunk_ids = request.chunk_ids or [str(i) for i in range(len(request.texts))]
    
    milvus_start = time.time()
    vectors = [
        {
            "doc_id": request.doc_id,
            "chunk_id": chunk_ids[i],
            "content": request.texts[i],
            "embedding": embeddings[i]
        }
        for i in range(len(request.texts))
    ]
    vector_ids = milvus_client.insert(vectors)
    milvus_time = (time.time() - milvus_start) * 1000

    es_start = time.time()
    es_documents = [
        {
            "doc_id": request.doc_id,
            "chunk_id": chunk_ids[i],
            "content": request.texts[i],
            "title": request.title,
            "keywords": request.keywords,
            "metadata": request.metadata,
            "milvus_id": vector_ids[i] if i < len(vector_ids) else ""
        }
        for i in range(len(request.texts))
    ]
    
    es_success = 0
    try:
        es_success = es_client.bulk_index(es_documents)
    except Exception as e:
        logger.error(f"Failed to index in Elasticsearch: {e}")
    es_time = (time.time() - es_start) * 1000

    total_time = (time.time() - start_time) * 1000

    logger.info(
        f"Dual storage embed: doc_id={request.doc_id}, "
        f"milvus={len(vector_ids)} vectors ({milvus_time:.1f}ms), "
        f"es={es_success} docs ({es_time:.1f}ms), "
        f"total={total_time:.1f}ms"
    )

    return {
        "vector_ids": vector_ids,
        "es_indexed": es_success,
        "dimension": len(embeddings[0]) if embeddings else 0,
        "milvus_time_ms": milvus_time,
        "es_time_ms": es_time,
        "total_time_ms": total_time
    }


@router.post("/search", response_model=SearchResponse)
async def search_vectors(request: SearchRequest):
    start_time = time.time()

    embedding_service = QwenEmbedding()
    query_vector = await embedding_service.embed(request.query)

    results = milvus_client.search(
        query_vector=query_vector,
        top_k=request.top_k,
        doc_ids=request.doc_ids
    )

    search_time = (time.time() - start_time) * 1000

    return SearchResponse(
        results=[SearchResult(**r) for r in results],
        search_time_ms=search_time
    )


@router.delete("/vectors")
async def delete_vectors(request: DeleteRequest):
    milvus_client.delete_by_doc_id(request.doc_id)
    
    try:
        es_client.delete_document(request.doc_id)
        logger.info(f"Deleted document from both storages: {request.doc_id}")
    except Exception as e:
        logger.warning(f"Failed to delete from Elasticsearch: {e}")
    
    return {"message": f"Deleted vectors for doc_id: {request.doc_id}"}


@router.delete("/vectors/dual")
async def delete_dual_storage(request: DeleteRequest):
    start_time = time.time()
    
    milvus_deleted = False
    es_deleted = False
    
    try:
        milvus_client.delete_by_doc_id(request.doc_id)
        milvus_deleted = True
    except Exception as e:
        logger.error(f"Failed to delete from Milvus: {e}")
    
    try:
        es_deleted = es_client.delete_document(request.doc_id)
    except Exception as e:
        logger.error(f"Failed to delete from Elasticsearch: {e}")
    
    total_time = (time.time() - start_time) * 1000
    
    return {
        "doc_id": request.doc_id,
        "milvus_deleted": milvus_deleted,
        "es_deleted": es_deleted,
        "time_ms": total_time
    }
