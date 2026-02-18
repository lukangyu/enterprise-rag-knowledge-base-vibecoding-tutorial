from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
import logging
import time

from services.kg.entity.entity_resolver import entity_resolver
from services.kg.graph.entity_repository import entity_repository
from services.kg.evidence.chain_builder import evidence_chain_builder
from services.kg.evidence.visualization import (
    visualization_data_generator,
    LayoutConfig,
    LayoutType
)
from models.entity import EntityType

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/kg", tags=["知识图谱-实体管理"])


class EntityResolveRequest(BaseModel):
    entity_name: str = Field(..., description="实体名称")
    context: Optional[str] = Field(default=None, description="上下文信息")
    entity_type: Optional[str] = Field(default=None, description="实体类型")
    candidate_limit: int = Field(default=5, ge=1, le=20, description="候选实体数量限制")


class EntityResolveResponse(BaseModel):
    entity_id: Optional[str] = Field(default=None, description="匹配的实体ID")
    entity_name: str = Field(description="实体名称")
    entity_type: str = Field(description="实体类型")
    is_new: bool = Field(description="是否为新实体")
    confidence: float = Field(description="匹配置信度")
    candidates: List[Dict[str, Any]] = Field(default_factory=list, description="候选实体列表")


class EntityDetailResponse(BaseModel):
    id: str
    name: str
    type: str
    description: Optional[str] = None
    properties: Dict[str, Any] = Field(default_factory=dict)
    confidence: float = 1.0
    source_doc_id: Optional[str] = None
    relations: List[Dict[str, Any]] = Field(default_factory=list)


class EntityListResponse(BaseModel):
    entities: List[Dict[str, Any]]
    total: int
    page: int
    size: int


@router.get("/entities", response_model=EntityListResponse)
async def list_entities(
    type: Optional[str] = Query(default=None, description="实体类型过滤"),
    keyword: Optional[str] = Query(default=None, description="关键词搜索"),
    source_doc_id: Optional[str] = Query(default=None, description="来源文档ID过滤"),
    min_confidence: float = Query(default=0.0, ge=0.0, le=1.0, description="最小置信度"),
    page: int = Query(default=1, ge=1, description="页码"),
    size: int = Query(default=20, ge=1, le=100, description="每页数量")
):
    start_time = time.time()
    
    try:
        skip = (page - 1) * size
        
        entities = []
        total = 0
        
        if keyword:
            entities = await entity_repository.search_entities(
                keyword=keyword,
                entity_type=type,
                skip=skip,
                limit=size
            )
        elif type:
            entities = await entity_repository.get_entities_by_type(
                entity_type=type,
                skip=skip,
                limit=size
            )
            total = await entity_repository.count_entities_by_type(type)
        else:
            entities = await entity_repository.get_entities_by_type(
                entity_type="",
                skip=skip,
                limit=size
            )
        
        if min_confidence > 0:
            entities = [
                e for e in entities
                if e.get("confidence", 1.0) >= min_confidence
            ]
        
        if source_doc_id:
            entities = [
                e for e in entities
                if e.get("source_doc_id") == source_doc_id
            ]
        
        if not total:
            total = len(entities)
        
        time_ms = (time.time() - start_time) * 1000
        logger.info(f"List entities: {len(entities)} results in {time_ms:.1f}ms")
        
        return EntityListResponse(
            entities=entities,
            total=total,
            page=page,
            size=size
        )
        
    except Exception as e:
        logger.error(f"Error listing entities: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/entities/{entity_id}", response_model=EntityDetailResponse)
async def get_entity(entity_id: str):
    start_time = time.time()
    
    try:
        entity = await entity_repository.get_entity_by_id(entity_id)
        
        if not entity:
            raise HTTPException(status_code=404, detail=f"Entity not found: {entity_id}")
        
        relations = await _get_entity_relations(entity_id)
        
        time_ms = (time.time() - start_time) * 1000
        logger.info(f"Get entity: {entity_id} in {time_ms:.1f}ms")
        
        return EntityDetailResponse(
            id=entity.get("id", ""),
            name=entity.get("name", ""),
            type=entity.get("type", ""),
            description=entity.get("description"),
            properties=entity.get("properties", {}),
            confidence=entity.get("confidence", 1.0),
            source_doc_id=entity.get("source_doc_id"),
            relations=relations
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting entity: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/entities/resolve", response_model=EntityResolveResponse)
async def resolve_entity(request: EntityResolveRequest):
    start_time = time.time()
    
    try:
        result = await entity_resolver.resolve(
            entity_name=request.entity_name,
            entity_type=request.entity_type,
            context=request.context,
            candidate_limit=request.candidate_limit
        )
        
        candidates_data = [
            {
                "entity_id": c.entity_id,
                "name": c.name,
                "type": c.entity_type,
                "similarity_score": c.similarity_score,
                "context_score": c.context_score,
                "final_score": c.final_score
            }
            for c in result.candidates
        ]
        
        time_ms = (time.time() - start_time) * 1000
        logger.info(f"Resolve entity: {request.entity_name} in {time_ms:.1f}ms")
        
        return EntityResolveResponse(
            entity_id=result.entity_id,
            entity_name=result.entity_name,
            entity_type=result.entity_type,
            is_new=result.is_new,
            confidence=result.confidence,
            candidates=candidates_data
        )
        
    except Exception as e:
        logger.error(f"Error resolving entity: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/entities/{entity_id}/evidence-chain")
async def get_evidence_chain(
    entity_id: str,
    end_entity_id: Optional[str] = Query(default=None, description="目标实体ID"),
    max_hops: int = Query(default=3, ge=1, le=10, description="最大跳数")
):
    start_time = time.time()
    
    try:
        chain = await evidence_chain_builder.build_chain(
            start_entity_id=entity_id,
            end_entity_id=end_entity_id,
            max_hops=max_hops
        )
        
        paths_data = []
        for path in chain.paths:
            paths_data.append({
                "nodes": [
                    {
                        "entity_id": n.entity_id,
                        "entity_name": n.entity_name,
                        "entity_type": n.entity_type
                    }
                    for n in path.nodes
                ],
                "edges": [
                    {
                        "relation_id": e.relation_id,
                        "relation_type": e.relation_type,
                        "head_entity_id": e.head_entity_id,
                        "tail_entity_id": e.tail_entity_id,
                        "confidence": e.confidence
                    }
                    for e in path.edges
                ],
                "length": path.length,
                "confidence": path.confidence
            })
        
        time_ms = (time.time() - start_time) * 1000
        logger.info(f"Build evidence chain: {entity_id} in {time_ms:.1f}ms")
        
        return {
            "chain_id": chain.chain_id,
            "start_entity": {
                "entity_id": chain.start_entity.entity_id,
                "entity_name": chain.start_entity.entity_name,
                "entity_type": chain.start_entity.entity_type
            },
            "end_entity": {
                "entity_id": chain.end_entity.entity_id,
                "entity_name": chain.end_entity.entity_name,
                "entity_type": chain.end_entity.entity_type
            } if chain.end_entity else None,
            "paths": paths_data,
            "total_confidence": chain.total_confidence,
            "source_documents": chain.source_documents
        }
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error building evidence chain: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/entities/{entity_id}/visualization")
async def get_entity_visualization(
    entity_id: str,
    max_hops: int = Query(default=2, ge=1, le=5, description="最大跳数"),
    layout: str = Query(default="force_directed", description="布局类型")
):
    start_time = time.time()
    
    try:
        chain = await evidence_chain_builder.build_chain(
            start_entity_id=entity_id,
            max_hops=max_hops
        )
        
        entities = []
        relations = []
        seen_entity_ids = set()
        seen_relation_ids = set()
        
        for path in chain.paths:
            for node in path.nodes:
                if node.entity_id not in seen_entity_ids:
                    entities.append({
                        "id": node.entity_id,
                        "name": node.entity_name,
                        "type": node.entity_type,
                        "properties": node.properties,
                        "confidence": 1.0
                    })
                    seen_entity_ids.add(node.entity_id)
            
            for edge in path.edges:
                if edge.relation_id not in seen_relation_ids:
                    relations.append({
                        "id": edge.relation_id,
                        "type": edge.relation_type,
                        "start_id": edge.head_entity_id,
                        "end_id": edge.tail_entity_id,
                        "confidence": edge.confidence
                    })
                    seen_relation_ids.add(edge.relation_id)
        
        layout_type = LayoutType.FORCE_DIRECTED
        if layout == "hierarchical":
            layout_type = LayoutType.HIERARCHICAL
        elif layout == "circular":
            layout_type = LayoutType.CIRCULAR
        elif layout == "grid":
            layout_type = LayoutType.GRID
        
        layout_config = LayoutConfig(
            layout_type=layout_type,
            width=800,
            height=600
        )
        
        graph_data = visualization_data_generator.generate_graph_data(
            entities=entities,
            relations=relations,
            layout_config=layout_config
        )
        
        result = visualization_data_generator.to_dict(graph_data)
        
        time_ms = (time.time() - start_time) * 1000
        logger.info(f"Generate visualization: {entity_id} in {time_ms:.1f}ms")
        
        return result
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error generating visualization: {e}")
        raise HTTPException(status_code=500, detail=str(e))


async def _get_entity_relations(entity_id: str) -> List[Dict[str, Any]]:
    from services.kg.graph.relation_repository import relation_repository
    
    relations = []
    
    try:
        outgoing = await relation_repository.get_relations_by_head_entity(entity_id)
        for rel in outgoing:
            relations.append({
                "id": rel.get("id"),
                "type": rel.get("relation_type"),
                "direction": "outgoing",
                "target_entity_id": rel.get("tail_entity_id"),
                "target_entity_name": rel.get("tail_entity_name"),
                "confidence": rel.get("confidence", 1.0)
            })
        
        incoming = await relation_repository.get_relations_by_tail_entity(entity_id)
        for rel in incoming:
            relations.append({
                "id": rel.get("id"),
                "type": rel.get("relation_type"),
                "direction": "incoming",
                "source_entity_id": rel.get("head_entity_id"),
                "source_entity_name": rel.get("head_entity_name"),
                "confidence": rel.get("confidence", 1.0)
            })
    except Exception as e:
        logger.error(f"Error getting entity relations: {e}")
    
    return relations
