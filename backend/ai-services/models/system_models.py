from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional
from enum import Enum
from datetime import datetime


class ConfigCategory(str, Enum):
    GENERAL = "general"
    SEARCH = "search"
    LLM = "llm"
    KG = "kg"
    STORAGE = "storage"


class SystemConfig(BaseModel):
    general: Dict[str, Any] = Field(default_factory=lambda: {
        "site_name": "GraphRAG知识库系统",
        "site_description": "企业级知识库问答系统",
        "max_upload_size": 52428800,
        "supported_formats": ["pdf", "docx", "md", "txt"]
    })
    search: Dict[str, Any] = Field(default_factory=lambda: {
        "default_top_k": 10,
        "max_top_k": 100,
        "default_threshold": 0.5,
        "enable_hybrid_search": True
    })
    llm: Dict[str, Any] = Field(default_factory=lambda: {
        "default_model": "qwen2.5-max",
        "max_tokens": 4096,
        "default_temperature": 0.7
    })
    kg: Dict[str, Any] = Field(default_factory=lambda: {
        "default_max_hops": 3,
        "default_min_confidence": 0.6,
        "enable_auto_extraction": True
    })
    storage: Dict[str, Any] = Field(default_factory=lambda: {
        "vector_db": "milvus",
        "graph_db": "neo4j",
        "doc_db": "elasticsearch"
    })


class ConfigUpdate(BaseModel):
    category: ConfigCategory
    key: str
    value: Any


class ComponentStatus(BaseModel):
    name: str
    status: str
    latency_ms: Optional[float] = None
    message: Optional[str] = None
    details: Optional[Dict[str, Any]] = None


class ResourceUsage(BaseModel):
    cpu_usage: float = Field(..., description="CPU使用率(%)")
    memory_usage: float = Field(..., description="内存使用率(%)")
    disk_usage: float = Field(..., description="磁盘使用率(%)")
    gpu_usage: Optional[float] = Field(None, description="GPU使用率(%)")


class SystemStatistics(BaseModel):
    total_documents: int = 0
    total_chunks: int = 0
    total_entities: int = 0
    total_relations: int = 0
    total_users: int = 0
    queries_today: int = 0


class SystemStatus(BaseModel):
    status: str
    version: str
    uptime: str
    components: List[ComponentStatus]
    resources: ResourceUsage
    statistics: SystemStatistics


class AuditLogCreate(BaseModel):
    user_id: str
    username: str
    action: str
    resource_type: str
    resource_id: Optional[str] = None
    details: Optional[Dict[str, Any]] = None
    ip_address: str = "unknown"
    user_agent: str = "unknown"
    status: str = "success"


class AuditLog(AuditLogCreate):
    id: str
    created_at: datetime

    class Config:
        from_attributes = True


class AuditLogQuery(BaseModel):
    page: int = Field(default=1, ge=1)
    size: int = Field(default=20, ge=1, le=100)
    action: Optional[str] = None
    user_id: Optional[str] = None
    resource_type: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None


class DocumentStats(BaseModel):
    total: int = 0
    new_this_period: int = 0
    by_type: Dict[str, int] = Field(default_factory=dict)
    by_status: Dict[str, int] = Field(default_factory=dict)


class QueryStats(BaseModel):
    total_queries: int = 0
    avg_response_time_ms: float = 0.0
    avg_satisfaction: float = 0.0
    by_day: List[Dict[str, Any]] = Field(default_factory=list)


class KGStats(BaseModel):
    total_entities: int = 0
    total_relations: int = 0
    entity_types: Dict[str, int] = Field(default_factory=dict)
    relation_types: Dict[str, int] = Field(default_factory=dict)


class UserStats(BaseModel):
    total_users: int = 0
    active_users: int = 0
    new_users_this_period: int = 0


class StatisticsResponse(BaseModel):
    period: str
    document_stats: DocumentStats
    query_stats: QueryStats
    kg_stats: KGStats
    user_stats: UserStats
