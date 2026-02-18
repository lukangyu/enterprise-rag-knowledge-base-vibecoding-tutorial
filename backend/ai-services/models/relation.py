from enum import Enum
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from uuid import uuid4


class RelationType(str, Enum):
    BELONGS_TO = "BELONGS_TO"
    CONTAINS = "CONTAINS"
    LOCATED_AT = "LOCATED_AT"
    CREATED_BY = "CREATED_BY"
    AFFECTS = "AFFECTS"
    DEPENDS_ON = "DEPENDS_ON"


class Relation(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    head_entity_id: str
    head_entity_name: str
    relation_type: RelationType
    tail_entity_id: str
    tail_entity_name: str
    evidence: Optional[str] = None
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    source_chunk_id: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.now)

    class Config:
        use_enum_values = True
