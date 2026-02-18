import asyncio
import logging
import time
from typing import List, Dict, Any, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum
from uuid import uuid4

from services.kg.entity.llm_extractor import LLMEntityExtractor, Entity
from services.kg.relation.llm_extractor import LLMRelationExtractor, Relation
from services.kg.entity.entity_processor import EntityProcessor, ProcessedEntity
from services.kg.relation.relation_processor import RelationProcessor, ProcessedRelation
from services.kg.graph.neo4j_client import neo4j_client
from services.kg.graph.entity_repository import entity_repository
from services.kg.graph.relation_repository import relation_repository
from config.kg_settings import kg_settings

logger = logging.getLogger(__name__)


class PipelineStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class ExtractionStage(str, Enum):
    ENTITY_EXTRACTION = "entity_extraction"
    RELATION_EXTRACTION = "relation_extraction"
    ENTITY_PROCESSING = "entity_processing"
    RELATION_PROCESSING = "relation_processing"
    GRAPH_STORAGE = "graph_storage"


@dataclass
class ExtractionProgress:
    stage: ExtractionStage
    total_items: int = 0
    processed_items: int = 0
    failed_items: int = 0
    start_time: float = field(default_factory=time.time)
    end_time: Optional[float] = None
    errors: List[str] = field(default_factory=list)

    @property
    def progress_percent(self) -> float:
        if self.total_items == 0:
            return 0.0
        return (self.processed_items / self.total_items) * 100

    @property
    def elapsed_time_ms(self) -> float:
        end = self.end_time or time.time()
        return (end - self.start_time) * 1000


@dataclass
class ExtractionConfig:
    entity_types: Optional[List[str]] = None
    relation_types: Optional[List[str]] = None
    min_confidence: float = 0.7
    deduplicate: bool = True
    merge_existing: bool = True
    batch_size: int = 10
    max_retries: int = 3


@dataclass
class ExtractionResult:
    doc_id: str
    entities: List[ProcessedEntity]
    relations: List[ProcessedRelation]
    entity_count: int
    relation_count: int
    extraction_time_ms: float
    status: PipelineStatus
    errors: List[str] = field(default_factory=list)


class KGExtractionPipeline:
    def __init__(self):
        self.entity_extractor = LLMEntityExtractor()
        self.relation_extractor = LLMRelationExtractor()
        self.entity_processor = EntityProcessor()
        self.relation_processor = RelationProcessor()
        self._progress_callbacks: List[Callable[[ExtractionProgress], None]] = []
        self._current_progress: Optional[ExtractionProgress] = None
        self._status: PipelineStatus = PipelineStatus.PENDING

    def register_progress_callback(self, callback: Callable[[ExtractionProgress], None]) -> None:
        self._progress_callbacks.append(callback)

    def _notify_progress(self, progress: ExtractionProgress) -> None:
        self._current_progress = progress
        for callback in self._progress_callbacks:
            try:
                callback(progress)
            except Exception as e:
                logger.error(f"Progress callback error: {e}")

    def _handle_error(self, error: Exception, stage: ExtractionStage, context: Dict[str, Any] = None) -> None:
        error_msg = f"Error in {stage.value}: {str(error)}"
        if context:
            error_msg += f" | Context: {context}"
        logger.error(error_msg)
        
        if self._current_progress:
            self._current_progress.errors.append(error_msg)
            self._current_progress.failed_items += 1

    async def extract_from_chunk(
        self,
        chunk_id: str,
        text: str,
        config: ExtractionConfig = None
    ) -> ExtractionResult:
        if config is None:
            config = ExtractionConfig()

        start_time = time.time()
        entities: List[ProcessedEntity] = []
        relations: List[ProcessedRelation] = []
        errors: List[str] = []

        try:
            if config.entity_types:
                entity_types_dict = {et: et for et in config.entity_types}
                raw_entities = await self.entity_extractor.extract_with_custom_types(text, entity_types_dict)
            else:
                raw_entities = await self.entity_extractor.extract(text)

            if config.deduplicate:
                processed = self.entity_processor.deduplicate(raw_entities)
            else:
                processed = [self.entity_processor.normalize_entity(e) for e in raw_entities]

            filtered_entities = self.entity_processor.filter_by_confidence(
                processed, config.min_confidence
            )
            entities = filtered_entities

            if entities:
                if config.relation_types:
                    relation_types_dict = {rt: rt for rt in config.relation_types}
                    raw_relations = await self.relation_extractor.extract_with_custom_types(
                        text, entities, relation_types_dict
                    )
                else:
                    raw_relations = await self.relation_extractor.extract(text, entities)

                valid_relations, invalid_relations = self.relation_processor.validate(
                    raw_relations, entities
                )

                if config.deduplicate:
                    processed_relations = self.relation_processor.deduplicate(valid_relations)
                else:
                    processed_relations = [
                        ProcessedRelation(
                            head=r.head,
                            head_normalized=r.head.lower().strip(),
                            relation=r.relation,
                            tail=r.tail,
                            tail_normalized=r.tail.lower().strip(),
                            evidence=r.evidence,
                            confidence=r.confidence,
                            properties=r.properties or {},
                            source_count=1
                        ) for r in valid_relations
                    ]

                relations = self.relation_processor.filter_low_confidence(
                    [Relation(
                        head=pr.head,
                        relation=pr.relation,
                        tail=pr.tail,
                        evidence=pr.evidence,
                        confidence=pr.confidence,
                        properties=pr.properties
                    ) for pr in processed_relations],
                    config.min_confidence
                )
                relations = [pr for pr in processed_relations if pr.confidence >= config.min_confidence]

        except Exception as e:
            self._handle_error(e, ExtractionStage.ENTITY_EXTRACTION, {"chunk_id": chunk_id})
            errors.append(str(e))

        extraction_time_ms = (time.time() - start_time) * 1000

        return ExtractionResult(
            doc_id=chunk_id,
            entities=entities,
            relations=relations,
            entity_count=len(entities),
            relation_count=len(relations),
            extraction_time_ms=extraction_time_ms,
            status=PipelineStatus.COMPLETED if not errors else PipelineStatus.FAILED,
            errors=errors
        )

    async def extract_from_document(
        self,
        doc_id: str,
        chunks: List[Dict[str, Any]],
        config: ExtractionConfig = None
    ) -> ExtractionResult:
        if config is None:
            config = ExtractionConfig()

        start_time = time.time()
        all_entities: List[ProcessedEntity] = []
        all_relations: List[ProcessedRelation] = []
        errors: List[str] = []

        progress = ExtractionProgress(
            stage=ExtractionStage.ENTITY_EXTRACTION,
            total_items=len(chunks)
        )
        self._notify_progress(progress)

        chunk_entities_map: Dict[str, List[ProcessedEntity]] = {}
        
        for i, chunk in enumerate(chunks):
            chunk_id = chunk.get("chunk_id", str(uuid4()))
            text = chunk.get("content", "")
            
            if not text:
                continue

            try:
                if config.entity_types:
                    entity_types_dict = {et: et for et in config.entity_types}
                    raw_entities = await self.entity_extractor.extract_with_custom_types(text, entity_types_dict)
                else:
                    raw_entities = await self.entity_extractor.extract(text)

                if config.deduplicate:
                    processed = self.entity_processor.deduplicate(raw_entities)
                else:
                    processed = [self.entity_processor.normalize_entity(e) for e in raw_entities]

                filtered = self.entity_processor.filter_by_confidence(
                    processed, config.min_confidence
                )
                chunk_entities_map[chunk_id] = filtered
                all_entities.extend(filtered)

            except Exception as e:
                self._handle_error(e, ExtractionStage.ENTITY_EXTRACTION, {"chunk_id": chunk_id})
                errors.append(str(e))

            progress.processed_items = i + 1
            self._notify_progress(progress)

        progress = ExtractionProgress(
            stage=ExtractionStage.RELATION_EXTRACTION,
            total_items=len(chunks)
        )
        self._notify_progress(progress)

        for i, chunk in enumerate(chunks):
            chunk_id = chunk.get("chunk_id", str(uuid4()))
            text = chunk.get("content", "")
            entities = chunk_entities_map.get(chunk_id, [])

            if not text or not entities:
                continue

            try:
                if config.relation_types:
                    relation_types_dict = {rt: rt for rt in config.relation_types}
                    raw_relations = await self.relation_extractor.extract_with_custom_types(
                        text, entities, relation_types_dict
                    )
                else:
                    raw_relations = await self.relation_extractor.extract(text, entities)

                valid_relations, _ = self.relation_processor.validate(raw_relations, entities)

                if config.deduplicate:
                    processed_relations = self.relation_processor.deduplicate(valid_relations)
                else:
                    processed_relations = [
                        ProcessedRelation(
                            head=r.head,
                            head_normalized=r.head.lower().strip(),
                            relation=r.relation,
                            tail=r.tail,
                            tail_normalized=r.tail.lower().strip(),
                            evidence=r.evidence,
                            confidence=r.confidence,
                            properties=r.properties or {},
                            source_count=1
                        ) for r in valid_relations
                    ]

                filtered_relations = [
                    pr for pr in processed_relations
                    if pr.confidence >= config.min_confidence
                ]
                all_relations.extend(filtered_relations)

            except Exception as e:
                self._handle_error(e, ExtractionStage.RELATION_EXTRACTION, {"chunk_id": chunk_id})
                errors.append(str(e))

            progress.processed_items = i + 1
            self._notify_progress(progress)

        if config.deduplicate:
            progress = ExtractionProgress(
                stage=ExtractionStage.ENTITY_PROCESSING,
                total_items=len(all_entities)
            )
            self._notify_progress(progress)
            
            entity_groups: Dict[str, List[ProcessedEntity]] = {}
            for entity in all_entities:
                key = f"{entity.type}_{entity.normalized_name}"
                if key not in entity_groups:
                    entity_groups[key] = []
                entity_groups[key].append(entity)

            deduplicated_entities: List[ProcessedEntity] = []
            for key, group in entity_groups.items():
                if len(group) == 1:
                    deduplicated_entities.append(group[0])
                else:
                    merged = self._merge_processed_entities(group)
                    deduplicated_entities.append(merged)

            all_entities = deduplicated_entities
            progress.processed_items = len(all_entities)
            self._notify_progress(progress)

            progress = ExtractionProgress(
                stage=ExtractionStage.RELATION_PROCESSING,
                total_items=len(all_relations)
            )
            self._notify_progress(progress)

            relation_map: Dict[str, ProcessedRelation] = {}
            for rel in all_relations:
                key = f"{rel.head_normalized}|{rel.relation}|{rel.tail_normalized}"
                if key in relation_map:
                    existing = relation_map[key]
                    existing.source_count += 1
                    if rel.evidence and rel.evidence not in existing.evidence:
                        existing.evidence = f"{existing.evidence}; {rel.evidence}"
                else:
                    relation_map[key] = rel

            all_relations = list(relation_map.values())
            progress.processed_items = len(all_relations)
            self._notify_progress(progress)

        extraction_time_ms = (time.time() - start_time) * 1000

        return ExtractionResult(
            doc_id=doc_id,
            entities=all_entities,
            relations=all_relations,
            entity_count=len(all_entities),
            relation_count=len(all_relations),
            extraction_time_ms=extraction_time_ms,
            status=PipelineStatus.COMPLETED if not errors else PipelineStatus.FAILED,
            errors=errors
        )

    def _merge_processed_entities(self, entities: List[ProcessedEntity]) -> ProcessedEntity:
        if not entities:
            raise ValueError("Entity list cannot be empty")

        primary = entities[0]
        descriptions = [primary.description] if primary.description else []
        aliases = list(primary.aliases)
        all_properties = dict(primary.properties)

        for entity in entities[1:]:
            if entity.description and entity.description not in descriptions:
                descriptions.append(entity.description)
            for alias in entity.aliases:
                if alias not in aliases and alias != primary.name:
                    aliases.append(alias)
            if entity.name != primary.name and entity.name not in aliases:
                aliases.append(entity.name)
            for k, v in entity.properties.items():
                if k not in all_properties:
                    all_properties[k] = v

        avg_confidence = sum(e.confidence for e in entities) / len(entities)
        total_source_count = sum(e.source_count for e in entities)

        return ProcessedEntity(
            name=primary.name,
            normalized_name=primary.normalized_name,
            type=primary.type,
            description=" ".join(descriptions),
            confidence=avg_confidence,
            properties=all_properties,
            aliases=aliases,
            source_count=total_source_count
        )

    async def run_pipeline(
        self,
        doc_id: str,
        chunks: List[Dict[str, Any]],
        config: ExtractionConfig = None
    ) -> ExtractionResult:
        if config is None:
            config = ExtractionConfig()

        self._status = PipelineStatus.RUNNING

        result = await self.extract_from_document(doc_id, chunks, config)

        if result.entities or result.relations:
            progress = ExtractionProgress(
                stage=ExtractionStage.GRAPH_STORAGE,
                total_items=len(result.entities) + len(result.relations)
            )
            self._notify_progress(progress)

            try:
                await self._store_to_graph(result, config, progress)
            except Exception as e:
                self._handle_error(e, ExtractionStage.GRAPH_STORAGE, {"doc_id": doc_id})
                result.errors.append(str(e))
                result.status = PipelineStatus.FAILED

        self._status = PipelineStatus.COMPLETED if not result.errors else PipelineStatus.FAILED
        return result

    async def _store_to_graph(
        self,
        result: ExtractionResult,
        config: ExtractionConfig,
        progress: ExtractionProgress
    ) -> None:
        entity_id_map: Dict[str, str] = {}

        for entity in result.entities:
            entity_id = str(uuid4())
            entity_id_map[entity.normalized_name] = entity_id

            properties = {
                "description": entity.description,
                "confidence": entity.confidence,
                "aliases": entity.aliases,
                "source_doc_id": result.doc_id,
                "source_count": entity.source_count
            }
            properties.update(entity.properties)

            if config.merge_existing:
                existing = await entity_repository.get_entity_by_name(entity.name)
                if existing:
                    entity_id = existing.get("id", entity_id)
                    entity_id_map[entity.normalized_name] = entity_id
                    await entity_repository.update_entity(entity_id, properties)
                else:
                    await entity_repository.create_entity(
                        entity_id=entity_id,
                        name=entity.name,
                        entity_type=entity.type,
                        properties=properties
                    )
            else:
                await entity_repository.create_entity(
                    entity_id=entity_id,
                    name=entity.name,
                    entity_type=entity.type,
                    properties=properties
                )

            progress.processed_items += 1
            self._notify_progress(progress)

        for relation in result.relations:
            head_id = entity_id_map.get(relation.head_normalized)
            tail_id = entity_id_map.get(relation.tail_normalized)

            if not head_id or not tail_id:
                logger.warning(f"Skipping relation: entity not found - {relation.head} -> {relation.tail}")
                continue

            relation_id = str(uuid4())
            properties = {
                "evidence": relation.evidence,
                "confidence": relation.confidence,
                "source_doc_id": result.doc_id,
                "source_count": relation.source_count
            }
            properties.update(relation.properties)

            await relation_repository.create_relation(
                relation_id=relation_id,
                source_id=head_id,
                target_id=tail_id,
                relation_type=relation.relation,
                properties=properties
            )

            progress.processed_items += 1
            self._notify_progress(progress)

    def track_progress(self) -> Optional[ExtractionProgress]:
        return self._current_progress

    @property
    def status(self) -> PipelineStatus:
        return self._status


kg_pipeline = KGExtractionPipeline()
