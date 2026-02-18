from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Optional, List


class KGSettings(BaseSettings):
    NEO4J_URI: str = "bolt://localhost:7687"
    NEO4J_USERNAME: str = "neo4j"
    NEO4J_PASSWORD: str = "password"
    NEO4J_DATABASE: str = "neo4j"
    NEO4J_MAX_CONNECTION_POOL_SIZE: int = Field(default=50, ge=1)
    NEO4J_CONNECTION_TIMEOUT: float = Field(default=30.0, ge=1.0)
    NEO4J_MAX_TRANSACTION_RETRY_TIME: float = Field(default=30.0, ge=1.0)

    LLM_API_KEY: str = ""
    LLM_MODEL_NAME: str = "qwen-max"
    LLM_API_BASE: str = "https://dashscope.aliyuncs.com/api/v1"

    ENTITY_TYPES: List[str] = Field(
        default=["Person", "Organization", "Location", "Product", "Event", "Concept"]
    )
    ENTITY_MIN_CONFIDENCE: float = Field(default=0.5, ge=0.0, le=1.0)

    RELATION_TYPES: List[str] = Field(
        default=["BELONGS_TO", "CONTAINS", "LOCATED_AT", "CREATED_BY", "AFFECTS", "DEPENDS_ON"]
    )
    RELATION_MIN_CONFIDENCE: float = Field(default=0.5, ge=0.0, le=1.0)

    MAX_HOPS: int = Field(default=3, ge=1, le=10)
    DEFAULT_LIMIT: int = Field(default=100, ge=1, le=1000)
    
    SIMILARITY_THRESHOLD: float = Field(default=0.85, ge=0.0, le=1.0)
    ENTITY_CONFIDENCE_THRESHOLD: float = Field(default=0.5, ge=0.0, le=1.0)

    class Config:
        env_file = ".env"
        env_prefix = "KG_"
        case_sensitive = True


kg_settings = KGSettings()
