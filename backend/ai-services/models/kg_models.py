from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from models.entity import Entity, EntityType
from models.relation import Relation, RelationType


class EntityQueryRequest(BaseModel):
    name: Optional[str] = None
    entity_type: Optional[EntityType] = None
    source_doc_id: Optional[str] = None
    min_confidence: Optional[float] = Field(default=0.0, ge=0.0, le=1.0)
    limit: Optional[int] = Field(default=100, ge=1, le=1000)
    offset: Optional[int] = Field(default=0, ge=0)


class EntityQueryResponse(BaseModel):
    entities: List[Entity]
    total: int


class RelationQueryRequest(BaseModel):
    head_entity_id: Optional[str] = None
    tail_entity_id: Optional[str] = None
    relation_type: Optional[RelationType] = None
    min_confidence: Optional[float] = Field(default=0.0, ge=0.0, le=1.0)
    limit: Optional[int] = Field(default=100, ge=1, le=1000)
    offset: Optional[int] = Field(default=0, ge=0)


class RelationQueryResponse(BaseModel):
    relations: List[Relation]
    total: int


class GraphTraversalRequest(BaseModel):
    start_entity_id: str
    max_hops: Optional[int] = Field(default=3, ge=1, le=10)
    relation_types: Optional[List[RelationType]] = None
    direction: Optional[str] = Field(default="both", pattern="^(out|in|both)$")
    limit: Optional[int] = Field(default=100, ge=1, le=1000)


class GraphNode(BaseModel):
    entity: Entity
    distance: int


class GraphEdge(BaseModel):
    relation: Relation
    distance: int


class GraphTraversalResponse(BaseModel):
    nodes: List[GraphNode]
    edges: List[GraphEdge]


class PathQueryRequest(BaseModel):
    start_entity_id: str
    end_entity_id: str
    max_hops: Optional[int] = Field(default=5, ge=1, le=10)
    relation_types: Optional[List[RelationType]] = None


class PathNode(BaseModel):
    entity_id: str
    entity_name: str
    entity_type: EntityType


class PathEdge(BaseModel):
    relation_id: str
    relation_type: RelationType
    head_entity_id: str
    tail_entity_id: str


class Path(BaseModel):
    nodes: List[PathNode]
    edges: List[PathEdge]
    length: int


class PathQueryResponse(BaseModel):
    paths: List[Path]
    total: int


class SubgraphQueryRequest(BaseModel):
    entity_ids: List[str] = Field(..., min_length=1)
    include_relations: Optional[bool] = True
    max_depth: Optional[int] = Field(default=1, ge=0, le=5)


class SubgraphQueryResponse(BaseModel):
    entities: List[Entity]
    relations: List[Relation]


class ExtractionRequest(BaseModel):
    text: str = Field(..., min_length=1)
    source_doc_id: Optional[str] = None
    source_chunk_id: Optional[str] = None
    entity_types: Optional[List[EntityType]] = None
    relation_types: Optional[List[RelationType]] = None


class ExtractionResponse(BaseModel):
    entities: List[Entity]
    relations: List[Relation]
    extraction_time_ms: float
