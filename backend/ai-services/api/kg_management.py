import asyncio
import logging
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Query, BackgroundTasks
from pydantic import BaseModel, Field
from datetime import datetime
from uuid import uuid4

from services.kg.pipeline.kg_pipeline import (
    KGExtractionPipeline,
    ExtractionConfig,
    ExtractionResult,
    ExtractionProgress,
    PipelineStatus
)
from services.kg.graph.statistics import (
    graph_statistics_service,
    EntityStats,
    RelationStats,
    GraphDensity,
    OverviewStats
)
from services.kg.graph.quality_evaluator import (
    graph_quality_evaluator,
    QualityReport
)
from services.kg.graph.entity_repository import entity_repository
from services.kg.graph.relation_repository import relation_repository

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/kg", tags=["知识图谱管理"])

extraction_tasks: Dict[str, Dict[str, Any]] = {}


class ExtractionConfigRequest(BaseModel):
    entity_types: Optional[List[str]] = Field(default=None, description="实体类型列表")
    relation_types: Optional[List[str]] = Field(default=None, description="关系类型列表")
    min_confidence: float = Field(default=0.7, ge=0.0, le=1.0, description="最小置信度阈值")
    deduplicate: bool = Field(default=True, description="是否去重")
    merge_existing: bool = Field(default=True, description="是否合并已存在实体")


class ExtractionRequest(BaseModel):
    doc_id: str = Field(..., description="文档ID")
    chunk_ids: Optional[List[str]] = Field(default=None, description="Chunk ID列表")
    config: Optional[ExtractionConfigRequest] = Field(default=None, description="抽取配置")


class ChunkData(BaseModel):
    chunk_id: str
    content: str


class ExtractionTaskRequest(BaseModel):
    doc_id: str = Field(..., description="文档ID")
    chunks: List[ChunkData] = Field(..., description="文档分块数据")
    config: Optional[ExtractionConfigRequest] = Field(default=None, description="抽取配置")


class EntityUpdateRequest(BaseModel):
    name: Optional[str] = Field(default=None, description="实体名称")
    type: Optional[str] = Field(default=None, description="实体类型")
    description: Optional[str] = Field(default=None, description="实体描述")
    properties: Optional[Dict[str, Any]] = Field(default=None, description="扩展属性")


class RelationUpdateRequest(BaseModel):
    type: Optional[str] = Field(default=None, description="关系类型")
    evidence: Optional[str] = Field(default=None, description="证据文本")
    properties: Optional[Dict[str, Any]] = Field(default=None, description="扩展属性")


class ExtractionResponse(BaseModel):
    task_id: str
    doc_id: str
    status: str
    message: str


class ExtractionStatusResponse(BaseModel):
    task_id: str
    doc_id: str
    status: str
    progress: Optional[Dict[str, Any]] = None
    result: Optional[Dict[str, Any]] = None
    errors: List[str] = []


class StatisticsResponse(BaseModel):
    entity_stats: Dict[str, Any]
    relation_stats: Dict[str, Any]
    graph_density: Dict[str, Any]
    overview: Dict[str, Any]


class QualityEvaluateResponse(BaseModel):
    overall_score: float
    level: str
    completeness: Dict[str, Any]
    consistency: Dict[str, Any]
    accuracy: Dict[str, Any]
    recommendations: List[str]
    generated_at: str


async def run_extraction_task(
    task_id: str,
    doc_id: str,
    chunks: List[Dict[str, Any]],
    config: ExtractionConfig
):
    try:
        extraction_tasks[task_id]["status"] = PipelineStatus.RUNNING.value
        
        pipeline = KGExtractionPipeline()
        
        def progress_callback(progress: ExtractionProgress):
            extraction_tasks[task_id]["progress"] = {
                "stage": progress.stage.value,
                "total_items": progress.total_items,
                "processed_items": progress.processed_items,
                "failed_items": progress.failed_items,
                "progress_percent": progress.progress_percent,
                "elapsed_time_ms": progress.elapsed_time_ms
            }
        
        pipeline.register_progress_callback(progress_callback)
        
        result = await pipeline.run_pipeline(doc_id, chunks, config)
        
        extraction_tasks[task_id]["status"] = result.status.value
        extraction_tasks[task_id]["result"] = {
            "entity_count": result.entity_count,
            "relation_count": result.relation_count,
            "extraction_time_ms": result.extraction_time_ms
        }
        extraction_tasks[task_id]["errors"] = result.errors
        
    except Exception as e:
        logger.error(f"Extraction task {task_id} failed: {e}")
        extraction_tasks[task_id]["status"] = PipelineStatus.FAILED.value
        extraction_tasks[task_id]["errors"] = [str(e)]


@router.post("/extract", response_model=ExtractionResponse)
async def extract_knowledge(
    request: ExtractionTaskRequest,
    background_tasks: BackgroundTasks
):
    task_id = str(uuid4())
    
    config = ExtractionConfig()
    if request.config:
        config = ExtractionConfig(
            entity_types=request.config.entity_types,
            relation_types=request.config.relation_types,
            min_confidence=request.config.min_confidence,
            deduplicate=request.config.deduplicate,
            merge_existing=request.config.merge_existing
        )
    
    chunks = [
        {"chunk_id": chunk.chunk_id, "content": chunk.content}
        for chunk in request.chunks
    ]
    
    extraction_tasks[task_id] = {
        "doc_id": request.doc_id,
        "status": PipelineStatus.PENDING.value,
        "progress": None,
        "result": None,
        "errors": []
    }
    
    background_tasks.add_task(
        run_extraction_task,
        task_id,
        request.doc_id,
        chunks,
        config
    )
    
    return ExtractionResponse(
        task_id=task_id,
        doc_id=request.doc_id,
        status=PipelineStatus.PENDING.value,
        message="知识抽取任务已创建，正在后台执行"
    )


@router.get("/extract/{task_id}", response_model=ExtractionStatusResponse)
async def get_extraction_status(task_id: str):
    if task_id not in extraction_tasks:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    task = extraction_tasks[task_id]
    
    return ExtractionStatusResponse(
        task_id=task_id,
        doc_id=task["doc_id"],
        status=task["status"],
        progress=task.get("progress"),
        result=task.get("result"),
        errors=task.get("errors", [])
    )


@router.get("/statistics", response_model=StatisticsResponse)
async def get_statistics():
    try:
        entity_stats = await graph_statistics_service.get_entity_stats()
        relation_stats = await graph_statistics_service.get_relation_stats()
        graph_density = await graph_statistics_service.get_graph_density()
        overview = await graph_statistics_service.get_overview_stats()
        
        return StatisticsResponse(
            entity_stats={
                "total_count": entity_stats.total_count,
                "type_distribution": entity_stats.type_distribution,
                "avg_confidence": entity_stats.avg_confidence,
                "avg_relations_per_entity": entity_stats.avg_relations_per_entity
            },
            relation_stats={
                "total_count": relation_stats.total_count,
                "type_distribution": relation_stats.type_distribution,
                "avg_confidence": relation_stats.avg_confidence,
                "avg_evidence_length": relation_stats.avg_evidence_length
            },
            graph_density={
                "node_count": graph_density.node_count,
                "edge_count": graph_density.edge_count,
                "density": graph_density.density,
                "max_possible_edges": graph_density.max_possible_edges,
                "connectivity_ratio": graph_density.connectivity_ratio
            },
            overview={
                "total_entities": overview.total_entities,
                "total_relations": overview.total_relations,
                "entity_types": overview.entity_types,
                "relation_types": overview.relation_types,
                "graph_density": overview.graph_density,
                "avg_entity_confidence": overview.avg_entity_confidence,
                "avg_relation_confidence": overview.avg_relation_confidence,
                "last_updated": overview.last_updated
            }
        )
    except Exception as e:
        logger.error(f"Failed to get statistics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/entities/{entity_id}")
async def get_entity(entity_id: str):
    try:
        entity = await entity_repository.get_entity_by_id(entity_id)
        if not entity:
            raise HTTPException(status_code=404, detail="实体不存在")
        return entity
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get entity: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/entities/{entity_id}")
async def update_entity(entity_id: str, request: EntityUpdateRequest):
    try:
        existing = await entity_repository.get_entity_by_id(entity_id)
        if not existing:
            raise HTTPException(status_code=404, detail="实体不存在")
        
        properties = {}
        if request.name is not None:
            properties["name"] = request.name
        if request.type is not None:
            properties["type"] = request.type
        if request.description is not None:
            properties["description"] = request.description
        if request.properties is not None:
            properties.update(request.properties)
        
        if not properties:
            raise HTTPException(status_code=400, detail="没有提供更新内容")
        
        updated = await entity_repository.update_entity(entity_id, properties)
        if not updated:
            raise HTTPException(status_code=500, detail="更新失败")
        
        return {
            "entity_id": entity_id,
            "status": "updated",
            "updated_at": datetime.utcnow().isoformat()
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update entity: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/entities/{entity_id}")
async def delete_entity(entity_id: str):
    try:
        deleted = await entity_repository.delete_entity(entity_id)
        if not deleted:
            raise HTTPException(status_code=404, detail="实体不存在或删除失败")
        
        return {
            "entity_id": entity_id,
            "status": "deleted"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete entity: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/relations/{relation_id}")
async def get_relation(relation_id: str):
    try:
        relation = await relation_repository.get_relation_by_id(relation_id)
        if not relation:
            raise HTTPException(status_code=404, detail="关系不存在")
        return relation
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get relation: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/relations/{relation_id}")
async def update_relation(relation_id: str, request: RelationUpdateRequest):
    try:
        existing = await relation_repository.get_relation_by_id(relation_id)
        if not existing:
            raise HTTPException(status_code=404, detail="关系不存在")
        
        properties = {}
        if request.type is not None:
            properties["type"] = request.type
        if request.evidence is not None:
            properties["evidence"] = request.evidence
        if request.properties is not None:
            properties.update(request.properties)
        
        if not properties:
            raise HTTPException(status_code=400, detail="没有提供更新内容")
        
        updated = await relation_repository.update_relation(relation_id, properties)
        if not updated:
            raise HTTPException(status_code=500, detail="更新失败")
        
        return {
            "relation_id": relation_id,
            "status": "updated",
            "updated_at": datetime.utcnow().isoformat()
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update relation: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/relations/{relation_id}")
async def delete_relation(relation_id: str):
    try:
        deleted = await relation_repository.delete_relation(relation_id)
        if not deleted:
            raise HTTPException(status_code=404, detail="关系不存在或删除失败")
        
        return {
            "relation_id": relation_id,
            "status": "deleted"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete relation: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/quality/evaluate", response_model=QualityEvaluateResponse)
async def evaluate_quality():
    try:
        report = await graph_quality_evaluator.generate_report()
        
        return QualityEvaluateResponse(
            overall_score=report.overall_score,
            level=report.level.value,
            completeness={
                "score": report.completeness.score,
                "entity_coverage": report.completeness.entity_coverage,
                "relation_coverage": report.completeness.relation_coverage,
                "property_completeness": report.completeness.property_completeness,
                "description_coverage": report.completeness.description_coverage,
                "details": report.completeness.details
            },
            consistency={
                "score": report.consistency.score,
                "type_consistency": report.consistency.type_consistency,
                "naming_consistency": report.consistency.naming_consistency,
                "relation_consistency": report.consistency.relation_consistency,
                "details": report.consistency.details
            },
            accuracy={
                "score": report.accuracy.score,
                "avg_entity_confidence": report.accuracy.avg_entity_confidence,
                "avg_relation_confidence": report.accuracy.avg_relation_confidence,
                "high_confidence_ratio": report.accuracy.high_confidence_ratio,
                "low_confidence_count": report.accuracy.low_confidence_count,
                "details": report.accuracy.details
            },
            recommendations=report.recommendations,
            generated_at=report.generated_at
        )
    except Exception as e:
        logger.error(f"Failed to evaluate quality: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/quality/entity/{entity_id}")
async def evaluate_entity_quality(entity_id: str):
    try:
        result = await graph_quality_evaluator.evaluate_entity_quality(entity_id)
        if "error" in result:
            raise HTTPException(status_code=404, detail=result["error"])
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to evaluate entity quality: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/quality/relation/{relation_id}")
async def evaluate_relation_quality(relation_id: str):
    try:
        result = await graph_quality_evaluator.evaluate_relation_quality(relation_id)
        if "error" in result:
            raise HTTPException(status_code=404, detail=result["error"])
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to evaluate relation quality: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/entities")
async def list_entities(
    entity_type: Optional[str] = Query(default=None, description="实体类型"),
    keyword: Optional[str] = Query(default=None, description="搜索关键词"),
    skip: int = Query(default=0, ge=0, description="跳过数量"),
    limit: int = Query(default=100, ge=1, le=1000, description="返回数量")
):
    try:
        if keyword:
            entities = await entity_repository.search_entities(
                keyword=keyword,
                entity_type=entity_type,
                skip=skip,
                limit=limit
            )
        elif entity_type:
            entities = await entity_repository.get_entities_by_type(
                entity_type=entity_type,
                skip=skip,
                limit=limit
            )
        else:
            entities = await entity_repository.search_entities(
                keyword="*",
                skip=skip,
                limit=limit
            )
        
        return {
            "entities": entities,
            "count": len(entities),
            "skip": skip,
            "limit": limit
        }
    except Exception as e:
        logger.error(f"Failed to list entities: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/relations")
async def list_relations(
    entity_id: Optional[str] = Query(default=None, description="实体ID"),
    relation_type: Optional[str] = Query(default=None, description="关系类型"),
    direction: str = Query(default="both", description="方向: outgoing, incoming, both"),
    skip: int = Query(default=0, ge=0, description="跳过数量"),
    limit: int = Query(default=100, ge=1, le=1000, description="返回数量")
):
    try:
        if entity_id:
            relations = await relation_repository.get_relations_by_entity(
                entity_id=entity_id,
                direction=direction,
                skip=skip,
                limit=limit
            )
        elif relation_type:
            relations = await relation_repository.get_relations_by_type(
                relation_type=relation_type,
                skip=skip,
                limit=limit
            )
        else:
            relations = []
        
        return {
            "relations": relations,
            "count": len(relations),
            "skip": skip,
            "limit": limit
        }
    except Exception as e:
        logger.error(f"Failed to list relations: {e}")
        raise HTTPException(status_code=500, detail=str(e))
