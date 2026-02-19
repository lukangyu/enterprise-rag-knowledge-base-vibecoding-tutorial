from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from enum import Enum


class MessageRole(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class ChatMessage(BaseModel):
    role: MessageRole
    content: str
    timestamp: Optional[str] = None


class SourceReference(BaseModel):
    source_id: str = Field(..., description="来源ID")
    doc_id: str = Field(..., description="文档ID")
    chunk_id: Optional[str] = Field(None, description="片段ID")
    content: str = Field(..., description="来源内容")
    score: float = Field(default=0.0, description="相关度分数")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="元数据")


class GraphContext(BaseModel):
    entities: List[Dict[str, Any]] = Field(default_factory=list, description="相关实体")
    relations: List[Dict[str, Any]] = Field(default_factory=list, description="相关关系")
    paths: List[Dict[str, Any]] = Field(default_factory=list, description="证据路径")


class ChatRequest(BaseModel):
    query: str = Field(..., description="用户问题", min_length=1, max_length=2000)
    conversation_id: Optional[str] = Field(None, description="会话ID")
    history: Optional[List[ChatMessage]] = Field(default=None, description="对话历史")
    top_k: int = Field(default=10, description="检索结果数量")
    use_graph: bool = Field(default=True, description="是否使用图谱检索")
    use_rerank: bool = Field(default=True, description="是否使用重排序")
    stream: bool = Field(default=True, description="是否流式输出")
    filters: Optional[Dict[str, Any]] = Field(default=None, description="过滤条件")


class AnnotatedContent(BaseModel):
    text: str = Field(..., description="回答文本")
    source_ids: List[str] = Field(default_factory=list, description="引用的来源ID列表")


class ChatResponse(BaseModel):
    answer: str = Field(..., description="回答内容")
    sources: List[SourceReference] = Field(default_factory=list, description="引用来源")
    graph_context: Optional[GraphContext] = Field(None, description="图谱上下文")
    conversation_id: str = Field(..., description="会话ID")
    query: str = Field(..., description="原始问题")
    latency_ms: float = Field(..., description="响应延迟(ms)")


class StreamChunk(BaseModel):
    type: str = Field(..., description="chunk类型: text/source/done/error")
    content: Optional[str] = Field(None, description="文本内容")
    source: Optional[SourceReference] = Field(None, description="来源信息")
    done: bool = Field(default=False, description="是否结束")
    error: Optional[str] = Field(None, description="错误信息")


class ContextBuildResult(BaseModel):
    context_text: str = Field(..., description="构建的上下文文本")
    sources: List[SourceReference] = Field(default_factory=list, description="来源列表")
    token_count: int = Field(default=0, description="token数量估计")
    truncated: bool = Field(default=False, description="是否被截断")
