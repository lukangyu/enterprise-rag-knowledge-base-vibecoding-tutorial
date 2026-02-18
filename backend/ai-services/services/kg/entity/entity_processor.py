import logging
import re
from typing import List, Dict, Any, Optional, Tuple
from difflib import SequenceMatcher
from dataclasses import dataclass

from services.kg.entity.llm_extractor import Entity
from config.kg_settings import kg_settings

logger = logging.getLogger(__name__)


@dataclass
class ProcessedEntity:
    name: str
    normalized_name: str
    type: str
    description: str
    confidence: float
    properties: Dict[str, Any]
    aliases: List[str]
    source_count: int

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "normalized_name": self.normalized_name,
            "type": self.type,
            "description": self.description,
            "confidence": self.confidence,
            "properties": self.properties,
            "aliases": self.aliases,
            "source_count": self.source_count
        }


class EntityProcessor:
    def __init__(self):
        self.similarity_threshold = kg_settings.SIMILARITY_THRESHOLD
        self.confidence_threshold = kg_settings.ENTITY_CONFIDENCE_THRESHOLD

    def _calculate_similarity(self, str1: str, str2: str) -> float:
        if not str1 or not str2:
            return 0.0
        return SequenceMatcher(None, str1.lower(), str2.lower()).ratio()

    def _normalize_name(self, name: str) -> str:
        normalized = re.sub(r'[^\w\s\u4e00-\u9fff]', '', name)
        normalized = re.sub(r'\s+', '', normalized)
        return normalized.lower().strip()

    def normalize_entity(self, entity: Entity) -> ProcessedEntity:
        normalized_name = self._normalize_name(entity.name)
        return ProcessedEntity(
            name=entity.name,
            normalized_name=normalized_name,
            type=entity.type,
            description=entity.description,
            confidence=entity.confidence,
            properties=entity.properties or {},
            aliases=[],
            source_count=1
        )

    def deduplicate(self, entities: List[Entity]) -> List[ProcessedEntity]:
        if not entities:
            return []

        processed_entities: List[ProcessedEntity] = []
        entity_groups: Dict[str, List[ProcessedEntity]] = {}

        for entity in entities:
            processed = self.normalize_entity(entity)
            type_key = f"{processed.type}_{processed.normalized_name[:3]}"

            if type_key not in entity_groups:
                entity_groups[type_key] = []

            merged = False
            for existing in entity_groups[type_key]:
                similarity = self._calculate_similarity(
                    existing.normalized_name,
                    processed.normalized_name
                )
                if similarity >= self.similarity_threshold:
                    existing.aliases.append(entity.name)
                    existing.source_count += 1
                    merged = True
                    break

            if not merged:
                entity_groups[type_key].append(processed)

        for group in entity_groups.values():
            processed_entities.extend(group)

        logger.info(f"实体去重: {len(entities)} -> {len(processed_entities)}")
        return processed_entities

    def merge(self, entities: List[Entity]) -> ProcessedEntity:
        if not entities:
            raise ValueError("实体列表不能为空")

        primary = entities[0]
        merged_properties: Dict[str, Any] = primary.properties or {}
        descriptions = [primary.description] if primary.description else []
        aliases = []

        for entity in entities[1:]:
            if entity.description and entity.description not in descriptions:
                descriptions.append(entity.description)

            if entity.name != primary.name:
                aliases.append(entity.name)

            if entity.properties:
                for key, value in entity.properties.items():
                    if key not in merged_properties:
                        merged_properties[key] = value

        merged_description = " ".join(descriptions)
        avg_confidence = sum(e.confidence for e in entities) / len(entities)

        return ProcessedEntity(
            name=primary.name,
            normalized_name=self._normalize_name(primary.name),
            type=primary.type,
            description=merged_description,
            confidence=avg_confidence,
            properties=merged_properties,
            aliases=aliases,
            source_count=len(entities)
        )

    def calculate_confidence(
        self,
        entity: Entity,
        context_length: int = 0,
        mention_count: int = 1
    ) -> float:
        base_confidence = entity.confidence

        if context_length > 0:
            context_factor = min(1.0, context_length / 1000)
            base_confidence *= (0.8 + 0.2 * context_factor)

        if mention_count > 1:
            mention_factor = min(1.0, 1 + (mention_count - 1) * 0.1)
            base_confidence *= mention_factor

        name_length = len(entity.name)
        if name_length < 2:
            base_confidence *= 0.5
        elif name_length > 50:
            base_confidence *= 0.8

        if not entity.description:
            base_confidence *= 0.9

        return min(1.0, max(0.0, base_confidence))

    def filter_by_confidence(
        self,
        entities: List[ProcessedEntity],
        threshold: float = None
    ) -> List[ProcessedEntity]:
        if threshold is None:
            threshold = self.confidence_threshold

        filtered = [
            entity for entity in entities
            if entity.confidence >= threshold
        ]
        logger.info(f"置信度过滤: {len(entities)} -> {len(filtered)}")
        return filtered

    def group_by_type(self, entities: List[ProcessedEntity]) -> Dict[str, List[ProcessedEntity]]:
        grouped: Dict[str, List[ProcessedEntity]] = {}
        for entity in entities:
            if entity.type not in grouped:
                grouped[entity.type] = []
            grouped[entity.type].append(entity)
        return grouped

    def process_batch(
        self,
        entities_list: List[List[Entity]]
    ) -> List[ProcessedEntity]:
        all_entities = []
        for entities in entities_list:
            all_entities.extend(entities)

        deduplicated = self.deduplicate(all_entities)
        filtered = self.filter_by_confidence(deduplicated)

        return filtered
