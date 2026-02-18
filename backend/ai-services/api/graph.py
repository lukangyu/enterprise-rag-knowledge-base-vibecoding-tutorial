from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
import time
import logging

from services.kg.graph.traversal_engine import traversal_engine
from services.kg.graph.multi_hop_query import multi_hop_query_service
from services.kg.graph.path_query import path_query_service
from services.kg.graph.entity_repository import entity_repository
from services.kg.graph.relation_repository import relation_repository

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/kg", tags=["知识图谱查询"])


class TraversalRequest(BaseModel):
    start_entity_id: Optional[str] = None
    start_entity_name: Optional[str] = None
    traversal_type: str = Field(default="bfs", pattern="^(bfs|dfs)$")
    max_hops: int = Field(default=3, ge=1, le=10)
    relation_types: Optional[List[str]] = None
    entity_types: Optional[List[str]] = None
    min_confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    limit: int = Field(default=50, ge=1, le=1000)
    return_paths: bool = False


class TraversalResponse(BaseModel):
    nodes: List[Dict[str, Any]]
    edges: List[Dict[str, Any]]
    paths: Optional[List[List[Dict[str, Any]]]] = None
    total_nodes: int
    total_edges: int
    traversal_time_ms: float


class PathRequest(BaseModel):
    source_entity: str
    target_entity: str
    max_hops: int = Field(default=4, ge=1, le=10)
    algorithm: str = Field(default="shortest", pattern="^(shortest|all|exact)$")
    exact_hops: Optional[int] = None
    min_confidence: float = Field(default=0.6, ge=0.0, le=1.0)
    relation_types: Optional[List[str]] = None
    limit: int = Field(default=10, ge=1, le=100)


class PathResponse(BaseModel):
    paths: List[Dict[str, Any]]
    total: int
    algorithm: str
    query_time_ms: float


class SubgraphRequest(BaseModel):
    entity_ids: List[str] = Field(..., min_length=1)
    include_relations: bool = True
    relation_types: Optional[List[str]] = None
    max_depth: int = Field(default=2, ge=0, le=5)
    layout: str = Field(default="force", pattern="^(force|hierarchical|circular)$")


class SubgraphResponse(BaseModel):
    entities: List[Dict[str, Any]]
    relations: List[Dict[str, Any]]
    total_entities: int
    total_relations: int
    query_time_ms: float


@router.post("/traverse", response_model=TraversalResponse)
async def traverse_graph(request: TraversalRequest):
    start_time = time.time()
    
    start_entity_id = request.start_entity_id
    if not start_entity_id and request.start_entity_name:
        entity = await entity_repository.get_entity_by_name(request.start_entity_name)
        if not entity:
            raise HTTPException(status_code=404, detail=f"Entity not found: {request.start_entity_name}")
        start_entity_id = entity.get("id")
    
    if not start_entity_id:
        raise HTTPException(status_code=400, detail="Either start_entity_id or start_entity_name is required")

    try:
        if request.traversal_type == "bfs":
            result = await traversal_engine.bfs_traverse(
                start_entity_id=start_entity_id,
                max_hops=request.max_hops,
                relation_types=request.relation_types,
                entity_types=request.entity_types,
                min_confidence=request.min_confidence,
                limit=request.limit,
                return_paths=request.return_paths
            )
        else:
            result = await traversal_engine.dfs_traverse(
                start_entity_id=start_entity_id,
                max_hops=request.max_hops,
                relation_types=request.relation_types,
                entity_types=request.entity_types,
                min_confidence=request.min_confidence,
                limit=request.limit,
                return_paths=request.return_paths
            )

        traversal_time_ms = (time.time() - start_time) * 1000
        
        logger.info(
            f"Graph traversal completed: type={request.traversal_type}, "
            f"nodes={result['total_nodes']}, edges={result['total_edges']}, "
            f"time={traversal_time_ms:.1f}ms"
        )

        return TraversalResponse(
            nodes=result["nodes"],
            edges=result["edges"],
            paths=result.get("paths"),
            total_nodes=result["total_nodes"],
            total_edges=result["total_edges"],
            traversal_time_ms=traversal_time_ms
        )
    except Exception as e:
        logger.error(f"Graph traversal failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/path", response_model=PathResponse)
async def query_path(request: PathRequest):
    start_time = time.time()

    try:
        if request.algorithm == "shortest":
            result = await path_query_service.find_shortest_path(
                source_entity=request.source_entity,
                target_entity=request.target_entity,
                relation_types=request.relation_types,
                min_confidence=request.min_confidence,
                max_hops=request.max_hops
            )
            paths = [result] if result else []
        elif request.algorithm == "exact" and request.exact_hops:
            result = await path_query_service.find_paths_with_hops(
                source_entity=request.source_entity,
                target_entity=request.target_entity,
                exact_hops=request.exact_hops,
                relation_types=request.relation_types,
                min_confidence=request.min_confidence,
                limit=request.limit
            )
            paths = result.get("paths", [])
        else:
            result = await path_query_service.find_all_paths(
                source_entity=request.source_entity,
                target_entity=request.target_entity,
                relation_types=request.relation_types,
                min_confidence=request.min_confidence,
                max_hops=request.max_hops,
                limit=request.limit
            )
            paths = result.get("paths", [])

        query_time_ms = (time.time() - start_time) * 1000
        
        logger.info(
            f"Path query completed: algorithm={request.algorithm}, "
            f"paths={len(paths)}, time={query_time_ms:.1f}ms"
        )

        return PathResponse(
            paths=paths,
            total=len(paths),
            algorithm=request.algorithm,
            query_time_ms=query_time_ms
        )
    except Exception as e:
        logger.error(f"Path query failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/subgraph", response_model=SubgraphResponse)
async def query_subgraph(request: SubgraphRequest):
    start_time = time.time()

    try:
        entities = []
        entity_ids_set = set(request.entity_ids)
        
        for entity_id in request.entity_ids:
            entity = await entity_repository.get_entity_by_id(entity_id)
            if entity:
                entities.append(entity)

        relations = []
        if request.include_relations:
            for entity_id in request.entity_ids:
                entity_relations = await relation_repository.get_relations_by_entity(
                    entity_id=entity_id,
                    direction="both",
                    limit=100
                )
                for rel in entity_relations:
                    source_id = rel.get("source", {}).get("id")
                    target_id = rel.get("target", {}).get("id")
                    
                    if request.relation_types:
                        rel_type = rel.get("relation", {}).get("type")
                        if rel_type not in request.relation_types:
                            continue
                    
                    if source_id in entity_ids_set or target_id in entity_ids_set:
                        relations.append(rel)

        if request.max_depth > 0:
            for hop in range(request.max_depth):
                new_entity_ids = set()
                for rel in relations:
                    source_id = rel.get("source", {}).get("id")
                    target_id = rel.get("target", {}).get("id")
                    
                    if source_id and source_id not in entity_ids_set:
                        new_entity_ids.add(source_id)
                    if target_id and target_id not in entity_ids_set:
                        new_entity_ids.add(target_id)
                
                for entity_id in new_entity_ids:
                    entity = await entity_repository.get_entity_by_id(entity_id)
                    if entity:
                        entities.append(entity)
                        entity_ids_set.add(entity_id)

        unique_relations = []
        seen_relation_ids = set()
        for rel in relations:
            rel_id = rel.get("relation", {}).get("id")
            if rel_id and rel_id not in seen_relation_ids:
                unique_relations.append(rel)
                seen_relation_ids.add(rel_id)

        query_time_ms = (time.time() - start_time) * 1000
        
        logger.info(
            f"Subgraph query completed: entities={len(entities)}, "
            f"relations={len(unique_relations)}, time={query_time_ms:.1f}ms"
        )

        return SubgraphResponse(
            entities=entities,
            relations=unique_relations,
            total_entities=len(entities),
            total_relations=len(unique_relations),
            query_time_ms=query_time_ms
        )
    except Exception as e:
        logger.error(f"Subgraph query failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/multi-hop")
async def multi_hop_query(
    start_entity_id: str,
    hops: int = 2,
    relation_types: Optional[List[str]] = None,
    entity_types: Optional[List[str]] = None,
    min_confidence: float = 0.0,
    limit: int = 100
):
    start_time = time.time()

    try:
        if hops == 2:
            result = await multi_hop_query_service.query_2hop(
                start_entity_id=start_entity_id,
                relation_types=relation_types,
                entity_types=entity_types,
                min_confidence=min_confidence,
                limit=limit
            )
        elif hops == 3:
            result = await multi_hop_query_service.query_3hop(
                start_entity_id=start_entity_id,
                relation_types=relation_types,
                entity_types=entity_types,
                min_confidence=min_confidence,
                limit=limit
            )
        elif hops == 4:
            result = await multi_hop_query_service.query_4hop(
                start_entity_id=start_entity_id,
                relation_types=relation_types,
                entity_types=entity_types,
                min_confidence=min_confidence,
                limit=limit
            )
        else:
            raise HTTPException(status_code=400, detail="Hops must be 2, 3, or 4")

        query_time_ms = (time.time() - start_time) * 1000
        result["query_time_ms"] = query_time_ms
        
        logger.info(f"Multi-hop query completed: hops={hops}, results={result['total']}, time={query_time_ms:.1f}ms")

        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Multi-hop query failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/neighbors/{entity_id}")
async def get_neighbors(
    entity_id: str,
    relation_types: Optional[List[str]] = None,
    direction: str = "both",
    min_confidence: float = 0.0,
    limit: int = 50
):
    start_time = time.time()

    try:
        neighbors = await traversal_engine.get_neighbors(
            entity_id=entity_id,
            relation_types=relation_types,
            direction=direction,
            min_confidence=min_confidence,
            limit=limit
        )

        query_time_ms = (time.time() - start_time) * 1000
        
        return {
            "entity_id": entity_id,
            "neighbors": neighbors,
            "total": len(neighbors),
            "query_time_ms": query_time_ms
        }
    except Exception as e:
        logger.error(f"Get neighbors failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
