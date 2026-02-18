import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum
import asyncio
import time


class PipelineStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class PipelineProgress:
    total_chunks: int = 0
    processed_chunks: int = 0
    total_entities: int = 0
    total_relations: int = 0
    current_stage: str = ""
    status: PipelineStatus = PipelineStatus.PENDING
    error_message: Optional[str] = None
    start_time: Optional[float] = None
    end_time: Optional[float] = None


class KGPipeline:
    def __init__(
        self,
        entity_extractor,
        relation_extractor,
        entity_processor,
        relation_processor,
        entity_repository,
        relation_repository
    ):
        self.entity_extractor = entity_extractor
        self.relation_extractor = relation_extractor
        self.entity_processor = entity_processor
        self.relation_processor = relation_processor
        self.entity_repository = entity_repository
        self.relation_repository = relation_repository
        self.progress = PipelineProgress()

    async def run_full_pipeline(
        self,
        text: str,
        source_doc_id: str = None,
        progress_callback=None
    ) -> Dict[str, Any]:
        self.progress = PipelineProgress(
            status=PipelineStatus.RUNNING,
            start_time=time.time()
        )
        
        try:
            self.progress.current_stage = "entity_extraction"
            if progress_callback:
                await progress_callback(self.progress)
            
            entities = await self.entity_extractor.extract(text)
            self.progress.total_entities = len(entities)
            
            if progress_callback:
                await progress_callback(self.progress)
            
            self.progress.current_stage = "entity_processing"
            processed_entities = self.entity_processor.deduplicate(entities)
            processed_entities = self.entity_processor.filter_by_confidence(processed_entities)
            
            self.progress.current_stage = "relation_extraction"
            if progress_callback:
                await progress_callback(self.progress)
            
            relations = await self.relation_extractor.extract(text, entities)
            self.progress.total_relations = len(relations)
            
            self.progress.current_stage = "relation_processing"
            processed_relations = self.relation_processor.deduplicate(relations)
            processed_relations = self.relation_processor.filter_low_confidence(processed_relations)
            
            self.progress.current_stage = "storage"
            if progress_callback:
                await progress_callback(self.progress)
            
            stored_entity_ids = []
            for entity in processed_entities:
                entity_id = str(uuid4())
                await self.entity_repository.create_entity(
                    entity_id=entity_id,
                    name=entity.name,
                    entity_type=entity.type,
                    properties={"confidence": entity.confidence, "description": entity.description}
                )
                stored_entity_ids.append(entity_id)
            
            stored_relation_ids = []
            for relation in processed_relations:
                relation_id = str(uuid4())
                await self.relation_repository.create_relation(
                    relation_id=relation_id,
                    source_id=relation.head_normalized,
                    target_id=relation.tail_normalized,
                    relation_type=relation.relation,
                    properties={"confidence": relation.confidence, "evidence": relation.evidence}
                )
                stored_relation_ids.append(relation_id)
            
            self.progress.status = PipelineStatus.COMPLETED
            self.progress.end_time = time.time()
            self.progress.current_stage = "completed"
            
            if progress_callback:
                await progress_callback(self.progress)
            
            return {
                "entity_ids": stored_entity_ids,
                "relation_ids": stored_relation_ids,
                "entity_count": len(stored_entity_ids),
                "relation_count": len(stored_relation_ids),
                "processing_time": self.progress.end_time - self.progress.start_time
            }
        
        except Exception as e:
            self.progress.status = PipelineStatus.FAILED
            self.progress.error_message = str(e)
            self.progress.end_time = time.time()
            
            if progress_callback:
                await progress_callback(self.progress)
            
            raise

    async def extract_from_chunk(
        self,
        chunk: Dict[str, Any],
        source_doc_id: str = None
    ) -> Dict[str, Any]:
        text = chunk.get("content", "")
        chunk_id = chunk.get("id", str(uuid4()))
        
        entities = await self.entity_extractor.extract(text)
        relations = await self.relation_extractor.extract(text, entities)
        
        processed_entities = self.entity_processor.deduplicate(entities)
        processed_relations = self.relation_processor.deduplicate(relations)
        
        return {
            "chunk_id": chunk_id,
            "entities": [e.to_dict() if hasattr(e, 'to_dict') else e for e in processed_entities],
            "relations": [r.to_dict() if hasattr(r, 'to_dict') else r for r in processed_relations]
        }

    async def extract_from_document(
        self,
        chunks: List[Dict[str, Any]],
        source_doc_id: str = None,
        progress_callback=None
    ) -> Dict[str, Any]:
        self.progress = PipelineProgress(
            total_chunks=len(chunks),
            status=PipelineStatus.RUNNING,
            start_time=time.time()
        )
        
        all_entities = []
        all_relations = []
        
        try:
            for i, chunk in enumerate(chunks):
                self.progress.current_stage = f"processing_chunk_{i+1}"
                self.progress.processed_chunks = i + 1
                
                if progress_callback:
                    await progress_callback(self.progress)
                
                result = await self.extract_from_chunk(chunk, source_doc_id)
                all_entities.extend(result.get("entities", []))
                all_relations.extend(result.get("relations", []))
            
            self.progress.current_stage = "deduplication"
            if progress_callback:
                await progress_callback(self.progress)
            
            final_entities = self.entity_processor.deduplicate(
                [self._dict_to_entity(e) for e in all_entities]
            )
            final_relations = self.relation_processor.deduplicate(
                [self._dict_to_relation(r) for r in all_relations]
            )
            
            self.progress.total_entities = len(final_entities)
            self.progress.total_relations = len(final_relations)
            self.progress.status = PipelineStatus.COMPLETED
            self.progress.end_time = time.time()
            
            return {
                "entities": [e.to_dict() for e in final_entities],
                "relations": [r.to_dict() for r in final_relations],
                "entity_count": len(final_entities),
                "relation_count": len(final_relations),
                "processing_time": self.progress.end_time - self.progress.start_time
            }
        
        except Exception as e:
            self.progress.status = PipelineStatus.FAILED
            self.progress.error_message = str(e)
            self.progress.end_time = time.time()
            raise

    def _dict_to_entity(self, data: Dict[str, Any]):
        from services.kg.entity.llm_extractor import Entity
        return Entity(
            name=data.get("name", ""),
            type=data.get("type", ""),
            description=data.get("description", ""),
            confidence=data.get("confidence", 1.0),
            properties=data.get("properties")
        )

    def _dict_to_relation(self, data: Dict[str, Any]):
        from services.kg.relation.llm_extractor import Relation
        return Relation(
            head=data.get("head", ""),
            relation=data.get("relation", ""),
            tail=data.get("tail", ""),
            evidence=data.get("evidence", ""),
            confidence=data.get("confidence", 1.0),
            properties=data.get("properties")
        )

    def get_progress(self) -> PipelineProgress:
        return self.progress


class TestKGPipeline:
    @pytest.fixture
    def pipeline(
        self,
        entity_extractor,
        relation_extractor,
        entity_processor,
        relation_processor,
        entity_repository,
        relation_repository
    ):
        return KGPipeline(
            entity_extractor=entity_extractor,
            relation_extractor=relation_extractor,
            entity_processor=entity_processor,
            relation_processor=relation_processor,
            entity_repository=entity_repository,
            relation_repository=relation_repository
        )

    @pytest.fixture
    def sample_chunks(self):
        return [
            {"id": "chunk-1", "content": "张三是阿里巴巴的工程师"},
            {"id": "chunk-2", "content": "阿里巴巴总部位于杭州"},
            {"id": "chunk-3", "content": "李四也在阿里巴巴工作"}
        ]

    @pytest.mark.asyncio
    async def test_full_pipeline(self, pipeline):
        mock_entities = [
            MagicMock(name="张三", type="Person", description="工程师", confidence=0.9, properties={}),
            MagicMock(name="阿里巴巴", type="Organization", description="公司", confidence=0.85, properties={})
        ]
        mock_processed_entities = [
            MagicMock(name="张三", normalized_name="张三", type="Person", description="工程师", confidence=0.9, properties={}, aliases=[], source_count=1),
            MagicMock(name="阿里巴巴", normalized_name="阿里巴巴", type="Organization", description="公司", confidence=0.85, properties={}, aliases=[], source_count=1)
        ]
        mock_relations = [
            MagicMock(head="张三", relation="BELONGS_TO", tail="阿里巴巴", evidence="证据", confidence=0.9, properties={})
        ]
        mock_processed_relations = [
            MagicMock(head="张三", head_normalized="张三", relation="BELONGS_TO", tail="阿里巴巴", tail_normalized="阿里巴巴", evidence="证据", confidence=0.9, properties={}, source_count=1)
        ]
        
        pipeline.entity_extractor.extract = AsyncMock(return_value=mock_entities)
        pipeline.entity_processor.deduplicate = MagicMock(return_value=mock_processed_entities)
        pipeline.entity_processor.filter_by_confidence = MagicMock(return_value=mock_processed_entities)
        pipeline.relation_extractor.extract = AsyncMock(return_value=mock_relations)
        pipeline.relation_processor.deduplicate = MagicMock(return_value=mock_processed_relations)
        pipeline.relation_processor.filter_low_confidence = MagicMock(return_value=mock_processed_relations)
        pipeline.entity_repository.create_entity = AsyncMock(return_value={"id": "test-id"})
        pipeline.relation_repository.create_relation = AsyncMock(return_value={"id": "test-rel-id"})
        
        result = await pipeline.run_full_pipeline("张三是阿里巴巴的工程师")
        
        assert "entity_ids" in result
        assert "relation_ids" in result
        assert result["entity_count"] == 2
        assert result["relation_count"] == 1
        assert pipeline.progress.status == PipelineStatus.COMPLETED

    @pytest.mark.asyncio
    async def test_full_pipeline_with_progress_tracking(self, pipeline):
        progress_updates = []
        
        async def progress_callback(progress):
            progress_updates.append({
                "stage": progress.current_stage,
                "status": progress.status
            })
        
        mock_entities = [MagicMock(name="张三", type="Person", description="", confidence=0.9, properties={})]
        mock_processed_entities = [MagicMock(name="张三", normalized_name="张三", type="Person", description="", confidence=0.9, properties={}, aliases=[], source_count=1)]
        mock_relations = []
        mock_processed_relations = []
        
        pipeline.entity_extractor.extract = AsyncMock(return_value=mock_entities)
        pipeline.entity_processor.deduplicate = MagicMock(return_value=mock_processed_entities)
        pipeline.entity_processor.filter_by_confidence = MagicMock(return_value=mock_processed_entities)
        pipeline.relation_extractor.extract = AsyncMock(return_value=mock_relations)
        pipeline.relation_processor.deduplicate = MagicMock(return_value=mock_processed_relations)
        pipeline.relation_processor.filter_low_confidence = MagicMock(return_value=mock_processed_relations)
        pipeline.entity_repository.create_entity = AsyncMock(return_value={"id": "test-id"})
        pipeline.relation_repository.create_relation = AsyncMock(return_value={"id": "test-id"})
        
        await pipeline.run_full_pipeline("测试文本", progress_callback=progress_callback)
        
        assert len(progress_updates) > 0
        stages = [u["stage"] for u in progress_updates]
        assert "entity_extraction" in stages
        assert "completed" in stages

    @pytest.mark.asyncio
    async def test_full_pipeline_error_handling(self, pipeline):
        pipeline.entity_extractor.extract = AsyncMock(side_effect=Exception("Extraction failed"))
        
        with pytest.raises(Exception):
            await pipeline.run_full_pipeline("测试文本")
        
        assert pipeline.progress.status == PipelineStatus.FAILED
        assert "Extraction failed" in pipeline.progress.error_message

    @pytest.mark.asyncio
    async def test_extract_from_chunk(self, pipeline):
        mock_entities = [
            MagicMock(name="张三", type="Person", description="工程师", confidence=0.9, properties={})
        ]
        mock_processed_entities = [
            MagicMock(
                name="张三",
                normalized_name="张三",
                type="Person",
                description="工程师",
                confidence=0.9,
                properties={},
                aliases=[],
                source_count=1,
                to_dict=MagicMock(return_value={"name": "张三", "type": "Person"})
            )
        ]
        mock_relations = []
        mock_processed_relations = []
        
        pipeline.entity_extractor.extract = AsyncMock(return_value=mock_entities)
        pipeline.entity_processor.deduplicate = MagicMock(return_value=mock_processed_entities)
        pipeline.relation_extractor.extract = AsyncMock(return_value=mock_relations)
        pipeline.relation_processor.deduplicate = MagicMock(return_value=mock_processed_relations)
        
        chunk = {"id": "chunk-1", "content": "张三是工程师"}
        result = await pipeline.extract_from_chunk(chunk)
        
        assert "chunk_id" in result
        assert "entities" in result
        assert "relations" in result
        assert result["chunk_id"] == "chunk-1"

    @pytest.mark.asyncio
    async def test_extract_from_chunk_empty_content(self, pipeline):
        pipeline.entity_extractor.extract = AsyncMock(return_value=[])
        pipeline.entity_processor.deduplicate = MagicMock(return_value=[])
        pipeline.relation_extractor.extract = AsyncMock(return_value=[])
        pipeline.relation_processor.deduplicate = MagicMock(return_value=[])
        
        chunk = {"id": "chunk-1", "content": ""}
        result = await pipeline.extract_from_chunk(chunk)
        
        assert result["entities"] == []
        assert result["relations"] == []

    @pytest.mark.asyncio
    async def test_extract_from_document(self, pipeline, sample_chunks):
        mock_entities = [MagicMock(name="张三", type="Person", description="", confidence=0.9, properties={})]
        mock_processed_entities = [
            MagicMock(
                name="张三",
                normalized_name="张三",
                type="Person",
                description="",
                confidence=0.9,
                properties={},
                aliases=[],
                source_count=1,
                to_dict=MagicMock(return_value={"name": "张三", "type": "Person"})
            )
        ]
        mock_relations = []
        mock_processed_relations = []
        
        pipeline.entity_extractor.extract = AsyncMock(return_value=mock_entities)
        pipeline.entity_processor.deduplicate = MagicMock(return_value=mock_processed_entities)
        pipeline.relation_extractor.extract = AsyncMock(return_value=mock_relations)
        pipeline.relation_processor.deduplicate = MagicMock(return_value=mock_processed_relations)
        
        result = await pipeline.extract_from_document(sample_chunks)
        
        assert "entities" in result
        assert "relations" in result
        assert "entity_count" in result
        assert "relation_count" in result
        assert pipeline.progress.total_chunks == 3
        assert pipeline.progress.processed_chunks == 3

    @pytest.mark.asyncio
    async def test_extract_from_document_with_progress(self, pipeline, sample_chunks):
        progress_updates = []
        
        async def progress_callback(progress):
            progress_updates.append(progress.processed_chunks)
        
        mock_entities = [MagicMock(name="张三", type="Person", description="", confidence=0.9, properties={})]
        mock_processed_entities = [
            MagicMock(
                name="张三",
                normalized_name="张三",
                type="Person",
                description="",
                confidence=0.9,
                properties={},
                aliases=[],
                source_count=1,
                to_dict=MagicMock(return_value={"name": "张三"})
            )
        ]
        
        pipeline.entity_extractor.extract = AsyncMock(return_value=mock_entities)
        pipeline.entity_processor.deduplicate = MagicMock(return_value=mock_processed_entities)
        pipeline.relation_extractor.extract = AsyncMock(return_value=[])
        pipeline.relation_processor.deduplicate = MagicMock(return_value=[])
        
        await pipeline.extract_from_document(sample_chunks, progress_callback=progress_callback)
        
        assert len(progress_updates) >= 3
        assert progress_updates[-1] == 3

    @pytest.mark.asyncio
    async def test_extract_from_document_error_handling(self, pipeline, sample_chunks):
        pipeline.entity_extractor.extract = AsyncMock(side_effect=Exception("Processing error"))
        
        with pytest.raises(Exception):
            await pipeline.extract_from_document(sample_chunks)
        
        assert pipeline.progress.status == PipelineStatus.FAILED

    @pytest.mark.asyncio
    async def test_get_progress(self, pipeline):
        progress = pipeline.get_progress()
        
        assert isinstance(progress, PipelineProgress)
        assert progress.status == PipelineStatus.PENDING

    @pytest.mark.asyncio
    async def test_pipeline_timing(self, pipeline):
        mock_entities = [MagicMock(name="张三", type="Person", description="", confidence=0.9, properties={})]
        mock_processed_entities = [
            MagicMock(
                name="张三",
                normalized_name="张三",
                type="Person",
                description="",
                confidence=0.9,
                properties={},
                aliases=[],
                source_count=1
            )
        ]
        
        pipeline.entity_extractor.extract = AsyncMock(return_value=mock_entities)
        pipeline.entity_processor.deduplicate = MagicMock(return_value=mock_processed_entities)
        pipeline.entity_processor.filter_by_confidence = MagicMock(return_value=mock_processed_entities)
        pipeline.relation_extractor.extract = AsyncMock(return_value=[])
        pipeline.relation_processor.deduplicate = MagicMock(return_value=[])
        pipeline.relation_processor.filter_low_confidence = MagicMock(return_value=[])
        pipeline.entity_repository.create_entity = AsyncMock(return_value={"id": "test-id"})
        pipeline.relation_repository.create_relation = AsyncMock(return_value={"id": "test-id"})
        
        result = await pipeline.run_full_pipeline("测试文本")
        
        assert "processing_time" in result
        assert result["processing_time"] >= 0

    @pytest.mark.asyncio
    async def test_pipeline_empty_text(self, pipeline):
        pipeline.entity_extractor.extract = AsyncMock(return_value=[])
        pipeline.entity_processor.deduplicate = MagicMock(return_value=[])
        pipeline.entity_processor.filter_by_confidence = MagicMock(return_value=[])
        pipeline.relation_extractor.extract = AsyncMock(return_value=[])
        pipeline.relation_processor.deduplicate = MagicMock(return_value=[])
        pipeline.relation_processor.filter_low_confidence = MagicMock(return_value=[])
        
        result = await pipeline.run_full_pipeline("")
        
        assert result["entity_count"] == 0
        assert result["relation_count"] == 0

    @pytest.mark.asyncio
    async def test_pipeline_multiple_entities_relations(self, pipeline):
        mock_entities = [
            MagicMock(name="张三", type="Person", description="", confidence=0.9, properties={}),
            MagicMock(name="阿里巴巴", type="Organization", description="", confidence=0.85, properties={}),
            MagicMock(name="杭州", type="Location", description="", confidence=0.8, properties={})
        ]
        mock_processed_entities = [
            MagicMock(name="张三", normalized_name="张三", type="Person", description="", confidence=0.9, properties={}, aliases=[], source_count=1),
            MagicMock(name="阿里巴巴", normalized_name="阿里巴巴", type="Organization", description="", confidence=0.85, properties={}, aliases=[], source_count=1),
            MagicMock(name="杭州", normalized_name="杭州", type="Location", description="", confidence=0.8, properties={}, aliases=[], source_count=1)
        ]
        mock_relations = [
            MagicMock(head="张三", relation="BELONGS_TO", tail="阿里巴巴", evidence="", confidence=0.9, properties={}),
            MagicMock(head="阿里巴巴", relation="LOCATED_AT", tail="杭州", evidence="", confidence=0.85, properties={})
        ]
        mock_processed_relations = [
            MagicMock(head="张三", head_normalized="张三", relation="BELONGS_TO", tail="阿里巴巴", tail_normalized="阿里巴巴", evidence="", confidence=0.9, properties={}, source_count=1),
            MagicMock(head="阿里巴巴", head_normalized="阿里巴巴", relation="LOCATED_AT", tail="杭州", tail_normalized="杭州", evidence="", confidence=0.85, properties={}, source_count=1)
        ]
        
        pipeline.entity_extractor.extract = AsyncMock(return_value=mock_entities)
        pipeline.entity_processor.deduplicate = MagicMock(return_value=mock_processed_entities)
        pipeline.entity_processor.filter_by_confidence = MagicMock(return_value=mock_processed_entities)
        pipeline.relation_extractor.extract = AsyncMock(return_value=mock_relations)
        pipeline.relation_processor.deduplicate = MagicMock(return_value=mock_processed_relations)
        pipeline.relation_processor.filter_low_confidence = MagicMock(return_value=mock_processed_relations)
        pipeline.entity_repository.create_entity = AsyncMock(return_value={"id": "test-id"})
        pipeline.relation_repository.create_relation = AsyncMock(return_value={"id": "test-id"})
        
        result = await pipeline.run_full_pipeline("张三在阿里巴巴工作，公司位于杭州")
        
        assert result["entity_count"] == 3
        assert result["relation_count"] == 2


class TestPipelineProgress:
    def test_progress_initialization(self):
        progress = PipelineProgress()
        
        assert progress.total_chunks == 0
        assert progress.processed_chunks == 0
        assert progress.total_entities == 0
        assert progress.total_relations == 0
        assert progress.current_stage == ""
        assert progress.status == PipelineStatus.PENDING
        assert progress.error_message is None
        assert progress.start_time is None
        assert progress.end_time is None

    def test_progress_status_enum(self):
        assert PipelineStatus.PENDING == "pending"
        assert PipelineStatus.RUNNING == "running"
        assert PipelineStatus.COMPLETED == "completed"
        assert PipelineStatus.FAILED == "failed"

    def test_progress_update(self):
        progress = PipelineProgress()
        progress.status = PipelineStatus.RUNNING
        progress.current_stage = "entity_extraction"
        progress.total_entities = 10
        progress.processed_chunks = 5
        
        assert progress.status == PipelineStatus.RUNNING
        assert progress.current_stage == "entity_extraction"
        assert progress.total_entities == 10
        assert progress.processed_chunks == 5
