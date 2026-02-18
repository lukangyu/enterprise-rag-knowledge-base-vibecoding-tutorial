from enum import Enum
from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional
from datetime import datetime
from uuid import uuid4


class EntityType(str, Enum):
    PERSON = "Person"
    ORGANIZATION = "Organization"
    LOCATION = "Location"
    PRODUCT = "Product"
    EVENT = "Event"
    CONCEPT = "Concept"


class Entity(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    name: str
    type: EntityType
    description: Optional[str] = None
    alias: List[str] = Field(default_factory=list)
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    properties: Dict[str, Any] = Field(default_factory=dict)
    source_doc_id: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.now)

    class Config:
        use_enum_values = True
