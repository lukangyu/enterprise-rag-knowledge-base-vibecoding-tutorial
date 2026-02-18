import logging
import re
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from difflib import SequenceMatcher

from services.kg.graph.entity_repository import entity_repository
from config.kg_settings import kg_settings

logger = logging.getLogger(__name__)


@dataclass
class CandidateEntity:
    entity_id: str
    name: str
    entity_type: str
    description: Optional[str]
    properties: Dict[str, Any]
    similarity_score: float
    context_score: float
    final_score: float


@dataclass
class ResolveResult:
    entity_id: Optional[str]
    entity_name: str
    entity_type: str
    is_new: bool
    confidence: float
    matched_entity: Optional[CandidateEntity]
    candidates: List[CandidateEntity]


class EntityResolver:
    def __init__(self):
        self.similarity_threshold = 0.85
        self.context_weight = 0.4
        self.name_weight = 0.6
        self.high_confidence_threshold = 0.9

    async def find_candidates(
        self,
        entity_name: str,
        entity_type: Optional[str] = None,
        limit: int = 5
    ) -> List[CandidateEntity]:
        candidates: List[CandidateEntity] = []
        
        try:
            keyword = self._build_search_keyword(entity_name)
            entities = await entity_repository.search_entities(
                keyword=keyword,
                entity_type=entity_type,
                skip=0,
                limit=limit * 2
            )
            
            for entity_data in entities:
                candidate = CandidateEntity(
                    entity_id=entity_data.get("id", ""),
                    name=entity_data.get("name", ""),
                    entity_type=entity_data.get("type", ""),
                    description=entity_data.get("description"),
                    properties=entity_data.get("properties", {}),
                    similarity_score=0.0,
                    context_score=0.0,
                    final_score=0.0
                )
                candidates.append(candidate)
            
            logger.info(f"Found {len(candidates)} candidates for entity: {entity_name}")
            
        except Exception as e:
            logger.error(f"Error finding candidates: {e}")
        
        return candidates[:limit]

    async def match_by_context(
        self,
        entity_name: str,
        context: str,
        candidates: List[CandidateEntity]
    ) -> List[CandidateEntity]:
        if not context or not candidates:
            return candidates
        
        context_lower = context.lower()
        context_words = set(re.findall(r'\w+', context_lower))
        
        for candidate in candidates:
            context_score = 0.0
            
            if candidate.description:
                desc_words = set(re.findall(r'\w+', candidate.description.lower()))
                overlap = len(context_words & desc_words)
                context_score = min(1.0, overlap / max(len(desc_words), 1))
            
            for prop_value in candidate.properties.values():
                if isinstance(prop_value, str):
                    prop_words = set(re.findall(r'\w+', prop_value.lower()))
                    overlap = len(context_words & prop_words)
                    prop_score = min(1.0, overlap / max(len(prop_words), 1))
                    context_score = max(context_score, prop_score)
            
            candidate.context_score = context_score
        
        return candidates

    def calculate_similarity(
        self,
        entity_name: str,
        candidates: List[CandidateEntity]
    ) -> List[CandidateEntity]:
        normalized_name = self._normalize_name(entity_name)
        
        for candidate in candidates:
            candidate_normalized = self._normalize_name(candidate.name)
            
            exact_match = normalized_name == candidate_normalized
            contains_match = normalized_name in candidate_normalized or candidate_normalized in normalized_name
            
            if exact_match:
                candidate.similarity_score = 1.0
            elif contains_match:
                candidate.similarity_score = 0.95
            else:
                ratio = SequenceMatcher(None, normalized_name, candidate_normalized).ratio()
                candidate.similarity_score = ratio
            
            candidate.final_score = (
                self.name_weight * candidate.similarity_score +
                self.context_weight * candidate.context_score
            )
        
        return sorted(candidates, key=lambda x: x.final_score, reverse=True)

    def select_best_match(
        self,
        candidates: List[CandidateEntity],
        threshold: Optional[float] = None
    ) -> Optional[CandidateEntity]:
        if not candidates:
            return None
        
        if threshold is None:
            threshold = self.similarity_threshold
        
        best_candidate = candidates[0]
        
        if best_candidate.final_score >= threshold:
            return best_candidate
        
        return None

    async def resolve(
        self,
        entity_name: str,
        entity_type: Optional[str] = None,
        context: Optional[str] = None,
        candidate_limit: int = 5
    ) -> ResolveResult:
        logger.info(f"Resolving entity: {entity_name}, type: {entity_type}")
        
        candidates = await self.find_candidates(
            entity_name=entity_name,
            entity_type=entity_type,
            limit=candidate_limit
        )
        
        if context:
            candidates = await self.match_by_context(
                entity_name=entity_name,
                context=context,
                candidates=candidates
            )
        
        candidates = self.calculate_similarity(
            entity_name=entity_name,
            candidates=candidates
        )
        
        best_match = self.select_best_match(candidates)
        
        if best_match:
            is_new = False
            confidence = best_match.final_score
            entity_id = best_match.entity_id
            resolved_type = best_match.entity_type
            
            logger.info(
                f"Entity resolved to existing: {entity_name} -> {best_match.name} "
                f"(score: {confidence:.3f})"
            )
        else:
            is_new = True
            confidence = 0.0
            entity_id = None
            resolved_type = entity_type or "Concept"
            
            logger.info(f"Entity resolved as new: {entity_name}")
        
        return ResolveResult(
            entity_id=entity_id,
            entity_name=entity_name,
            entity_type=resolved_type,
            is_new=is_new,
            confidence=confidence,
            matched_entity=best_match,
            candidates=candidates
        )

    async def batch_resolve(
        self,
        entities: List[Dict[str, Any]],
        context: Optional[str] = None
    ) -> List[ResolveResult]:
        results: List[ResolveResult] = []
        
        for entity in entities:
            result = await self.resolve(
                entity_name=entity.get("name", ""),
                entity_type=entity.get("type"),
                context=context or entity.get("context"),
                candidate_limit=entity.get("candidate_limit", 5)
            )
            results.append(result)
        
        return results

    def _normalize_name(self, name: str) -> str:
        normalized = re.sub(r'[^\w\s\u4e00-\u9fff]', '', name)
        normalized = re.sub(r'\s+', '', normalized)
        return normalized.lower().strip()

    def _build_search_keyword(self, name: str) -> str:
        normalized = self._normalize_name(name)
        if len(normalized) >= 2:
            return f"*{normalized}*"
        return normalized

    def calculate_resolution_accuracy(
        self,
        results: List[ResolveResult],
        ground_truth: Dict[str, str]
    ) -> float:
        if not results or not ground_truth:
            return 0.0
        
        correct = 0
        total = 0
        
        for result in results:
            expected_id = ground_truth.get(result.entity_name)
            if expected_id:
                total += 1
                if result.entity_id == expected_id:
                    correct += 1
        
        return correct / total if total > 0 else 0.0


entity_resolver = EntityResolver()
