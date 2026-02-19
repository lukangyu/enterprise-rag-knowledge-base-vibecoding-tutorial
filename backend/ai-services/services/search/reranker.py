import httpx
import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from tenacity import retry, stop_after_attempt, wait_exponential

from config.settings import settings

logger = logging.getLogger(__name__)


@dataclass
class RerankResult:
    index: int
    relevance_score: float
    document: Dict[str, Any]


class RerankerService:
    RERANKER_API_URL = "https://dashscope.aliyuncs.com/api/v1/services/rerank/rerank"
    
    def __init__(
        self,
        api_key: str = None,
        model: str = "gte-rerank",
        top_n: int = 10,
        timeout: float = 30.0
    ):
        self.api_key = api_key or settings.QWEN_API_KEY
        self.model = model
        self.default_top_n = top_n
        self.timeout = timeout
    
    async def rerank(
        self,
        query: str,
        documents: List[Dict[str, Any]],
        top_n: int = None,
        return_documents: bool = True,
        min_score: float = 0.0
    ) -> List[Dict[str, Any]]:
        if not documents:
            return []
        
        if not self.api_key:
            logger.warning("Reranker API key not configured, returning original order")
            return documents[:top_n or self.default_top_n]
        
        top_n = top_n or self.default_top_n
        top_n = min(top_n, len(documents))
        
        doc_texts = []
        for doc in documents:
            text = doc.get("content", doc.get("text", ""))
            if text:
                doc_texts.append(text)
        
        if not doc_texts:
            return documents[:top_n]
        
        try:
            results = await self._call_reranker_api(query, doc_texts, top_n)
            
            reranked_docs = []
            for result in results:
                idx = result.index
                score = result.relevance_score
                
                if score < min_score:
                    continue
                
                doc = documents[idx].copy()
                doc["rerank_score"] = score
                doc["original_index"] = idx
                reranked_docs.append(doc)
            
            logger.info(
                f"Reranked {len(documents)} documents, "
                f"returned {len(reranked_docs)} with min_score={min_score}"
            )
            
            return reranked_docs
            
        except Exception as e:
            logger.error(f"Rerank failed: {e}, returning original order")
            return documents[:top_n]
    
    async def rerank_with_scores(
        self,
        query: str,
        documents: List[Dict[str, Any]],
        top_n: int = None
    ) -> List[RerankResult]:
        if not documents or not self.api_key:
            return []
        
        top_n = top_n or self.default_top_n
        
        doc_texts = [
            doc.get("content", doc.get("text", ""))
            for doc in documents
        ]
        
        return await self._call_reranker_api(query, doc_texts, top_n)
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10)
    )
    async def _call_reranker_api(
        self,
        query: str,
        documents: List[str],
        top_n: int
    ) -> List[RerankResult]:
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                self.RERANKER_API_URL,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": self.model,
                    "input": {
                        "query": query,
                        "documents": documents
                    },
                    "parameters": {
                        "top_n": min(top_n, len(documents)),
                        "return_documents": False
                    }
                }
            )
            
            if response.status_code != 200:
                raise Exception(f"Reranker API error: {response.status_code} - {response.text}")
            
            data = response.json()
            results = []
            
            output = data.get("output", {})
            rerank_results = output.get("results", [])
            
            for item in rerank_results:
                results.append(RerankResult(
                    index=item.get("index", 0),
                    relevance_score=item.get("relevance_score", 0.0),
                    document={}
                ))
            
            return results
    
    async def compute_relevance_scores(
        self,
        query: str,
        documents: List[str]
    ) -> List[float]:
        if not documents or not self.api_key:
            return [0.0] * len(documents)
        
        try:
            results = await self._call_reranker_api(query, documents, len(documents))
            
            scores = [0.0] * len(documents)
            for result in results:
                if 0 <= result.index < len(scores):
                    scores[result.index] = result.relevance_score
            
            return scores
            
        except Exception as e:
            logger.error(f"Compute relevance scores failed: {e}")
            return [0.0] * len(documents)


reranker_service = RerankerService()
