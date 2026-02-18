from fastapi import APIRouter, Query, HTTPException, status
from typing import Optional, List

from models.relation import Relation, RelationType
from models.kg_models import RelationQueryRequest, RelationQueryResponse
from services.kg.graph.relation_repository import relation_repository
from exceptions.kg_exceptions import RelationNotFoundException, EntityNotFoundException

router = APIRouter(prefix="/api/v1/kg/relations", tags=["relations"])


@router.get("", response_model=RelationQueryResponse)
async def query_relations(
    head_entity_id: Optional[str] = Query(None, description="Head entity ID filter"),
    tail_entity_id: Optional[str] = Query(None, description="Tail entity ID filter"),
    relation_type: Optional[RelationType] = Query(None, description="Relation type filter"),
    min_confidence: float = Query(0.0, ge=0.0, le=1.0, description="Minimum confidence"),
    limit: int = Query(100, ge=1, le=1000, description="Result limit"),
    offset: int = Query(0, ge=0, description="Result offset")
) -> RelationQueryResponse:
    if head_entity_id:
        relations_data = await relation_repository.get_relations_by_entity(
            entity_id=head_entity_id,
            direction="outgoing",
            skip=offset,
            limit=limit
        )
    elif tail_entity_id:
        relations_data = await relation_repository.get_relations_by_entity(
            entity_id=tail_entity_id,
            direction="incoming",
            skip=offset,
            limit=limit
        )
    elif relation_type:
        relations_data = await relation_repository.get_relations_by_type(
            relation_type=relation_type.value,
            skip=offset,
            limit=limit
        )
    else:
        relations_data = await relation_repository.get_relations_by_type(
            relation_type="*",
            skip=offset,
            limit=limit
        )

    relations = []
    for data in relations_data:
        rel_data = data.get("relation", {})
        if rel_data.get("confidence", 1.0) >= min_confidence:
            relations.append(Relation(
                id=rel_data.get("id"),
                head_entity_id=data.get("source", {}).get("id"),
                head_entity_name=data.get("source", {}).get("name"),
                relation_type=rel_data.get("type"),
                tail_entity_id=data.get("target", {}).get("id"),
                tail_entity_name=data.get("target", {}).get("name"),
                evidence=rel_data.get("evidence"),
                confidence=rel_data.get("confidence", 1.0),
                source_chunk_id=rel_data.get("source_chunk_id")
            ))

    return RelationQueryResponse(
        relations=relations,
        total=len(relations)
    )


@router.get("/{relation_id}")
async def get_relation(relation_id: str):
    relation_data = await relation_repository.get_relation_by_id(relation_id)
    
    if not relation_data:
        raise RelationNotFoundException(relation_id)
    
    rel = relation_data.get("relation", {})
    return {
        "id": rel.get("id"),
        "head_entity": relation_data.get("source"),
        "relation_type": rel.get("type"),
        "tail_entity": relation_data.get("target"),
        "evidence": rel.get("evidence"),
        "confidence": rel.get("confidence", 1.0),
        "source_chunk_id": rel.get("source_chunk_id"),
        "created_at": rel.get("created_at"),
        "updated_at": rel.get("updated_at")
    }


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_relation(relation: Relation):
    from services.kg.graph.entity_repository import entity_repository
    
    head_entity = await entity_repository.get_entity_by_id(relation.head_entity_id)
    if not head_entity:
        raise EntityNotFoundException(relation.head_entity_id)
    
    tail_entity = await entity_repository.get_entity_by_id(relation.tail_entity_id)
    if not tail_entity:
        raise EntityNotFoundException(relation.tail_entity_id)
    
    result = await relation_repository.create_relation(
        relation_id=relation.id,
        source_id=relation.head_entity_id,
        target_id=relation.tail_entity_id,
        relation_type=relation.relation_type.value if isinstance(relation.relation_type, RelationType) else relation.relation_type,
        properties={
            "evidence": relation.evidence,
            "confidence": relation.confidence,
            "source_chunk_id": relation.source_chunk_id
        }
    )
    
    return {
        "id": relation.id,
        "head_entity_id": relation.head_entity_id,
        "tail_entity_id": relation.tail_entity_id,
        "relation_type": relation.relation_type,
        "status": "created"
    }


@router.delete("/{relation_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_relation(relation_id: str) -> None:
    deleted = await relation_repository.delete_relation(relation_id)
    if not deleted:
        raise RelationNotFoundException(relation_id)
