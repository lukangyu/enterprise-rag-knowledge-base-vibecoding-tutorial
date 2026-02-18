import logging
from typing import List, Dict, Any, Set, Optional, Tuple
from dataclasses import dataclass

from services.kg.relation.llm_extractor import Relation
from config.kg_settings import kg_settings

logger = logging.getLogger(__name__)


@dataclass
class ProcessedRelation:
    head: str
    head_normalized: str
    relation: str
    tail: str
    tail_normalized: str
    evidence: str
    confidence: float
    properties: Dict[str, Any]
    source_count: int

    def to_dict(self) -> Dict[str, Any]:
        return {
            "head": self.head,
            "head_normalized": self.head_normalized,
            "relation": self.relation,
            "tail": self.tail,
            "tail_normalized": self.tail_normalized,
            "evidence": self.evidence,
            "confidence": self.confidence,
            "properties": self.properties,
            "source_count": self.source_count
        }


class RelationProcessor:
    def __init__(self):
        self.confidence_threshold = kg_settings.RELATION_CONFIDENCE_THRESHOLD

    def _normalize_entity_name(self, name: str) -> str:
        return name.lower().strip()

    def validate(
        self,
        relations: List[Relation],
        valid_entities: List[Any]
    ) -> Tuple[List[Relation], List[Relation]]:
        valid_entity_names: Set[str] = set()
        for entity in valid_entities:
            if hasattr(entity, 'name'):
                valid_entity_names.add(entity.name.lower().strip())
                if hasattr(entity, 'normalized_name'):
                    valid_entity_names.add(entity.normalized_name)
            elif isinstance(entity, dict):
                name = entity.get('name', '')
                if name:
                    valid_entity_names.add(name.lower().strip())
                normalized = entity.get('normalized_name', '')
                if normalized:
                    valid_entity_names.add(normalized)

        valid_relations: List[Relation] = []
        invalid_relations: List[Relation] = []

        for relation in relations:
            head_normalized = self._normalize_entity_name(relation.head)
            tail_normalized = self._normalize_entity_name(relation.tail)

            head_valid = head_normalized in valid_entity_names
            tail_valid = tail_normalized in valid_entity_names

            if head_valid and tail_valid:
                valid_relations.append(relation)
            else:
                invalid_relations.append(relation)
                if not head_valid:
                    logger.debug(f"头实体不存在: {relation.head}")
                if not tail_valid:
                    logger.debug(f"尾实体不存在: {relation.tail}")

        logger.info(f"关系验证: {len(valid_relations)} 有效, {len(invalid_relations)} 无效")
        return valid_relations, invalid_relations

    def filter_low_confidence(
        self,
        relations: List[Relation],
        threshold: float = None
    ) -> List[Relation]:
        if threshold is None:
            threshold = self.confidence_threshold

        filtered = [
            relation for relation in relations
            if relation.confidence >= threshold
        ]
        logger.info(f"置信度过滤: {len(relations)} -> {len(filtered)}")
        return filtered

    def deduplicate(self, relations: List[Relation]) -> List[ProcessedRelation]:
        if not relations:
            return []

        relation_map: Dict[str, ProcessedRelation] = {}

        for relation in relations:
            head_norm = self._normalize_entity_name(relation.head)
            tail_norm = self._normalize_entity_name(relation.tail)
            key = f"{head_norm}|{relation.relation}|{tail_norm}"

            if key in relation_map:
                existing = relation_map[key]
                existing.source_count += 1
                existing.confidence = min(1.0, existing.confidence + 0.1)

                if relation.evidence and relation.evidence not in existing.evidence:
                    existing.evidence = f"{existing.evidence}; {relation.evidence}"

                if relation.properties:
                    for k, v in relation.properties.items():
                        if k not in existing.properties:
                            existing.properties[k] = v
            else:
                relation_map[key] = ProcessedRelation(
                    head=relation.head,
                    head_normalized=head_norm,
                    relation=relation.relation,
                    tail=relation.tail,
                    tail_normalized=tail_norm,
                    evidence=relation.evidence,
                    confidence=relation.confidence,
                    properties=relation.properties or {},
                    source_count=1
                )

        result = list(relation_map.values())
        logger.info(f"关系去重: {len(relations)} -> {len(result)}")
        return result

    def calculate_confidence(
        self,
        relation: Relation,
        evidence_length: int = 0,
        co_occurrence_count: int = 1
    ) -> float:
        base_confidence = relation.confidence

        if relation.evidence:
            evidence_factor = min(1.0, len(relation.evidence) / 100)
            base_confidence *= (0.9 + 0.1 * evidence_factor)
        else:
            base_confidence *= 0.7

        if co_occurrence_count > 1:
            co_occurrence_factor = min(1.0, 1 + (co_occurrence_count - 1) * 0.05)
            base_confidence *= co_occurrence_factor

        head_len = len(relation.head)
        tail_len = len(relation.tail)
        if head_len < 2 or tail_len < 2:
            base_confidence *= 0.8

        return min(1.0, max(0.0, base_confidence))

    def group_by_type(
        self,
        relations: List[ProcessedRelation]
    ) -> Dict[str, List[ProcessedRelation]]:
        grouped: Dict[str, List[ProcessedRelation]] = {}
        for relation in relations:
            if relation.relation not in grouped:
                grouped[relation.relation] = []
            grouped[relation.relation].append(relation)
        return grouped

    def build_adjacency_list(
        self,
        relations: List[ProcessedRelation]
    ) -> Dict[str, List[Tuple[str, str]]]:
        adjacency: Dict[str, List[Tuple[str, str]]] = {}
        for relation in relations:
            if relation.head_normalized not in adjacency:
                adjacency[relation.head_normalized] = []
            adjacency[relation.head_normalized].append(
                (relation.relation, relation.tail_normalized)
            )
        return adjacency

    def process_batch(
        self,
        relations_list: List[List[Relation]],
        valid_entities: List[Any] = None
    ) -> List[ProcessedRelation]:
        all_relations = []
        for relations in relations_list:
            all_relations.extend(relations)

        if valid_entities:
            all_relations, _ = self.validate(all_relations, valid_entities)

        filtered = self.filter_low_confidence(all_relations)
        deduplicated = self.deduplicate(filtered)

        return deduplicated
