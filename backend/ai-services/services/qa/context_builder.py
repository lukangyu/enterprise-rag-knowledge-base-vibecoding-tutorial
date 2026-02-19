import logging
from typing import List, Dict, Any, Optional
from models.qa_models import SourceReference, GraphContext, ContextBuildResult
from config.settings import settings

logger = logging.getLogger(__name__)


class ContextBuilder:
    MAX_CONTEXT_TOKENS = 4000
    CHARS_PER_TOKEN = 2
    
    def __init__(
        self,
        max_context_tokens: int = None,
        max_source_length: int = 500
    ):
        self.max_context_tokens = max_context_tokens or self.MAX_CONTEXT_TOKENS
        self.max_source_length = max_source_length
    
    def build_context(
        self,
        query: str,
        search_results: List[Dict[str, Any]],
        graph_context: Optional[GraphContext] = None,
        history: Optional[List[Dict[str, Any]]] = None
    ) -> ContextBuildResult:
        logger.info(f"Building context for query: {query[:50]}...")
        
        sources: List[SourceReference] = []
        context_parts: List[str] = []
        current_tokens = 0
        truncated = False
        
        if history:
            history_text = self._format_history(history)
            history_tokens = self._estimate_tokens(history_text)
            if history_tokens < self.max_context_tokens * 0.3:
                context_parts.append(f"【对话历史】\n{history_text}")
                current_tokens += history_tokens
        
        if search_results:
            search_context, search_sources, search_tokens, was_truncated = self._format_search_results(
                search_results,
                remaining_tokens=self.max_context_tokens - current_tokens
            )
            if search_context:
                context_parts.append(search_context)
                sources.extend(search_sources)
                current_tokens += search_tokens
                if was_truncated:
                    truncated = True
        
        if graph_context and current_tokens < self.max_context_tokens:
            graph_text = self._format_graph_context(graph_context)
            graph_tokens = self._estimate_tokens(graph_text)
            remaining = self.max_context_tokens - current_tokens
            
            if graph_tokens <= remaining:
                context_parts.append(graph_text)
                current_tokens += graph_tokens
            else:
                truncated_graph = self._truncate_text(graph_text, remaining)
                context_parts.append(truncated_graph)
                current_tokens += self._estimate_tokens(truncated_graph)
                truncated = True
        
        context_text = "\n\n".join(context_parts)
        
        logger.info(
            f"Context built: {len(sources)} sources, "
            f"~{current_tokens} tokens, truncated={truncated}"
        )
        
        return ContextBuildResult(
            context_text=context_text,
            sources=sources,
            token_count=current_tokens,
            truncated=truncated
        )
    
    def _format_search_results(
        self,
        results: List[Dict[str, Any]],
        remaining_tokens: int
    ) -> tuple[str, List[SourceReference], int, bool]:
        if not results:
            return "", [], 0, False
        
        sources: List[SourceReference] = []
        formatted_parts: List[str] = []
        current_tokens = 0
        truncated = False
        
        for i, result in enumerate(results, 1):
            doc_id = result.get("doc_id", "")
            chunk_id = result.get("chunk_id", "")
            content = result.get("content", "")
            score = result.get("score", result.get("_score", 0.0))
            metadata = result.get("metadata", {})
            
            if len(content) > self.max_source_length:
                content = content[:self.max_source_length] + "..."
            
            source_id = f"[{i}]"
            source = SourceReference(
                source_id=source_id,
                doc_id=doc_id,
                chunk_id=chunk_id,
                content=content,
                score=score,
                metadata=metadata
            )
            sources.append(source)
            
            formatted_text = f"{source_id} {content}"
            text_tokens = self._estimate_tokens(formatted_text)
            
            if current_tokens + text_tokens <= remaining_tokens:
                formatted_parts.append(formatted_text)
                current_tokens += text_tokens
            else:
                remaining = remaining_tokens - current_tokens
                if remaining > 50:
                    truncated_text = self._truncate_text(formatted_text, remaining)
                    formatted_parts.append(truncated_text)
                    current_tokens += self._estimate_tokens(truncated_text)
                truncated = True
                break
        
        if formatted_parts:
            header = "【相关文档片段】\n"
            header_tokens = self._estimate_tokens(header)
            context = header + "\n".join(formatted_parts)
            return context, sources, current_tokens + header_tokens, truncated
        
        return "", sources, current_tokens, truncated
    
    def _format_graph_context(self, graph_context: GraphContext) -> str:
        parts = []
        
        entities = graph_context.entities or []
        if entities:
            entity_lines = []
            for entity in entities[:10]:
                name = entity.get("name", "")
                entity_type = entity.get("type", "")
                description = entity.get("description", "")
                entity_lines.append(f"  - {name}（{entity_type}）: {description[:100]}")
            parts.append("【相关实体】\n" + "\n".join(entity_lines))
        
        relations = graph_context.relations or []
        if relations:
            relation_lines = []
            for rel in relations[:10]:
                head = rel.get("head", "")
                relation_type = rel.get("type", rel.get("relation_type", ""))
                tail = rel.get("tail", "")
                relation_lines.append(f"  - {head} --[{relation_type}]--> {tail}")
            parts.append("【相关关系】\n" + "\n".join(relation_lines))
        
        paths = graph_context.paths or []
        if paths:
            path_lines = []
            for path in paths[:3]:
                nodes = path.get("nodes", [])
                path_str = " -> ".join([n.get("name", n.get("entity_name", "")) for n in nodes])
                path_lines.append(f"  - {path_str}")
            parts.append("【证据路径】\n" + "\n".join(path_lines))
        
        return "\n\n".join(parts)
    
    def _format_history(self, history: List[Dict[str, Any]]) -> str:
        lines = []
        for msg in history[-5:]:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            if role == "user":
                lines.append(f"用户: {content}")
            else:
                lines.append(f"助手: {content}")
        return "\n".join(lines)
    
    def _estimate_tokens(self, text: str) -> int:
        return len(text) // self.CHARS_PER_TOKEN
    
    def _truncate_text(self, text: str, max_tokens: int) -> str:
        max_chars = max_tokens * self.CHARS_PER_TOKEN
        if len(text) <= max_chars:
            return text
        return text[:max_chars] + "..."


context_builder = ContextBuilder()
