from typing import List, Dict, Any
from collections import defaultdict
import logging
from config.settings import settings

logger = logging.getLogger(__name__)


class RRFFusion:
    def __init__(self, k: int = None):
        self.k = k or settings.RRF_K

    def fuse(
        self,
        keyword_results: List[Dict[str, Any]],
        vector_results: List[Dict[str, Any]],
        k: int = None
    ) -> List[Dict[str, Any]]:
        k = k or self.k
        scores = defaultdict(float)
        result_map = {}

        for rank, result in enumerate(keyword_results, 1):
            doc_id = result.get("doc_id", result.get("_id", str(rank)))
            score = 1.0 / (k + rank)
            scores[doc_id] += score
            
            if doc_id not in result_map:
                result_map[doc_id] = result.copy()
                result_map[doc_id]["keyword_rank"] = rank
                result_map[doc_id]["keyword_score"] = result.get("_score", 0)
            
            logger.debug(f"Keyword rank {rank}: doc_id={doc_id}, score contribution={score}")

        for rank, result in enumerate(vector_results, 1):
            doc_id = result.get("doc_id", result.get("id", str(rank)))
            score = 1.0 / (k + rank)
            scores[doc_id] += score
            
            if doc_id not in result_map:
                result_map[doc_id] = result.copy()
            else:
                if not result_map[doc_id].get("content") and result.get("content"):
                    result_map[doc_id]["content"] = result.get("content")
            
            result_map[doc_id]["vector_rank"] = rank
            result_map[doc_id]["vector_score"] = result.get("score", result.get("_score", 0))
            
            logger.debug(f"Vector rank {rank}: doc_id={doc_id}, score contribution={score}")

        fused_results = sorted(
            [{"doc_id": k, "rrf_score": v, **result_map[k]} for k, v in scores.items()],
            key=lambda x: x["rrf_score"],
            reverse=True
        )

        for i, result in enumerate(fused_results, 1):
            result["rank"] = i

        logger.info(f"RRF fusion completed: {len(fused_results)} results fused with k={k}")
        return fused_results

    def weighted_fuse(
        self,
        keyword_results: List[Dict[str, Any]],
        vector_results: List[Dict[str, Any]],
        keyword_weight: float = 0.3,
        vector_weight: float = 0.7
    ) -> List[Dict[str, Any]]:
        scores = defaultdict(float)
        result_map = {}

        max_keyword_score = max(
            (r.get("_score", r.get("score", 0)) for r in keyword_results),
            default=1.0
        )
        
        max_vector_score = max(
            (r.get("_score", r.get("score", 0)) for r in vector_results),
            default=1.0
        )

        for result in keyword_results:
            doc_id = result.get("doc_id", result.get("_id", ""))
            raw_score = result.get("_score", result.get("score", 0))
            normalized_score = raw_score / max_keyword_score if max_keyword_score > 0 else 0
            weighted_score = normalized_score * keyword_weight
            scores[doc_id] += weighted_score
            
            if doc_id not in result_map:
                result_map[doc_id] = result.copy()

        for result in vector_results:
            doc_id = result.get("doc_id", result.get("id", ""))
            raw_score = result.get("_score", result.get("score", 0))
            normalized_score = raw_score / max_vector_score if max_vector_score > 0 else 0
            weighted_score = normalized_score * vector_weight
            scores[doc_id] += weighted_score
            
            if doc_id not in result_map:
                result_map[doc_id] = result.copy()

        fused_results = sorted(
            [{"doc_id": k, "weighted_score": v, **result_map[k]} for k, v in scores.items()],
            key=lambda x: x["weighted_score"],
            reverse=True
        )

        for i, result in enumerate(fused_results, 1):
            result["rank"] = i

        logger.info(f"Weighted fusion completed: {len(fused_results)} results")
        return fused_results


rrf_fusion = RRFFusion()
