import httpx
import json
import logging
import re
from typing import AsyncGenerator, List, Dict, Any, Optional
from dataclasses import dataclass
from tenacity import retry, stop_after_attempt, wait_exponential

from config.settings import settings
from models.qa_models import SourceReference, StreamChunk

logger = logging.getLogger(__name__)


@dataclass
class LLMConfig:
    api_url: str = "https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation"
    model: str = "qwen-max"
    max_tokens: int = 2000
    temperature: float = 0.7
    timeout: float = 60.0


class SSEStreamHandler:
    def __init__(self, config: Optional[LLMConfig] = None):
        self.config = config or LLMConfig()
        self.api_key = settings.QWEN_API_KEY
    
    async def stream_generate(
        self,
        query: str,
        context: str,
        sources: List[SourceReference],
        system_prompt: str = None,
        history: List[Dict[str, str]] = None
    ) -> AsyncGenerator[str, None]:
        logger.info(f"Starting stream generation for query: {query[:50]}...")
        
        if not self.api_key:
            yield self._format_sse(StreamChunk(
                type="error",
                error="LLM API key not configured"
            ))
            return
        
        messages = self._build_messages(query, context, system_prompt, history)
        
        try:
            async for chunk in self._call_llm_stream(messages):
                yield chunk
            
            yield self._format_sse(StreamChunk(
                type="source",
                source=sources[0] if sources else None
            ))
            
            for source in sources:
                yield self._format_sse(StreamChunk(
                    type="source",
                    source=source
                ))
            
            yield self._format_sse(StreamChunk(
                type="done",
                done=True
            ))
            
        except Exception as e:
            logger.error(f"Stream generation error: {e}")
            yield self._format_sse(StreamChunk(
                type="error",
                error=str(e)
            ))
    
    async def generate(
        self,
        query: str,
        context: str,
        system_prompt: str = None,
        history: List[Dict[str, str]] = None
    ) -> str:
        logger.info(f"Starting non-stream generation for query: {query[:50]}...")
        
        if not self.api_key:
            raise ValueError("LLM API key not configured")
        
        messages = self._build_messages(query, context, system_prompt, history)
        
        try:
            response_text = await self._call_llm(messages)
            return response_text
        except Exception as e:
            logger.error(f"Generation error: {e}")
            raise
    
    def _build_messages(
        self,
        query: str,
        context: str,
        system_prompt: str = None,
        history: List[Dict[str, str]] = None
    ) -> List[Dict[str, str]]:
        messages = []
        
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        else:
            messages.append({
                "role": "system",
                "content": "你是一个专业的知识库问答助手。请根据提供的上下文信息准确回答用户问题，并在回答中标注引用来源。"
            })
        
        if history:
            for msg in history[-6:]:
                messages.append({
                    "role": msg.get("role", "user"),
                    "content": msg.get("content", "")
                })
        
        user_content = f"""请根据以下上下文信息回答问题。

## 上下文信息
{context}

## 用户问题
{query}

## 回答要求
1. 基于上下文信息准确回答问题
2. 如果上下文中没有相关信息，请明确说明"根据现有知识库，我无法找到相关信息"
3. 在回答中标注引用来源，格式为 [1]、[2] 等
4. 回答要简洁、准确、有条理

请直接回答问题："""
        
        messages.append({"role": "user", "content": user_content})
        return messages
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10)
    )
    async def _call_llm_stream(
        self,
        messages: List[Dict[str, str]]
    ) -> AsyncGenerator[str, None]:
        async with httpx.AsyncClient(timeout=self.config.timeout) as client:
            response = await client.post(
                self.config.api_url,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                    "X-DashScope-SSE": "enable"
                },
                json={
                    "model": self.config.model,
                    "messages": messages,
                    "max_tokens": self.config.max_tokens,
                    "temperature": self.config.temperature,
                    "stream": True,
                    "incremental_output": True
                }
            )
            
            if response.status_code != 200:
                raise Exception(f"LLM API error: {response.status_code} - {response.text}")
            
            buffer = ""
            async for line in response.aiter_lines():
                if not line:
                    continue
                
                if line.startswith("data:"):
                    data_str = line[5:].strip()
                    if data_str == "[DONE]":
                        break
                    
                    try:
                        data = json.loads(data_str)
                        choices = data.get("choices", [])
                        if choices:
                            delta = choices[0].get("message", {})
                            content = delta.get("content", "")
                            if content:
                                yield self._format_sse(StreamChunk(
                                    type="text",
                                    content=content
                                ))
                    except json.JSONDecodeError:
                        continue
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10)
    )
    async def _call_llm(self, messages: List[Dict[str, str]]) -> str:
        async with httpx.AsyncClient(timeout=self.config.timeout) as client:
            response = await client.post(
                self.config.api_url,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": self.config.model,
                    "messages": messages,
                    "max_tokens": self.config.max_tokens,
                    "temperature": self.config.temperature
                }
            )
            
            if response.status_code != 200:
                raise Exception(f"LLM API error: {response.status_code} - {response.text}")
            
            data = response.json()
            choices = data.get("choices", [])
            if choices:
                return choices[0].get("message", {}).get("content", "")
            return ""
    
    def _format_sse(self, chunk: StreamChunk) -> str:
        return f"data: {chunk.model_dump_json()}\n\n"


sse_stream_handler = SSEStreamHandler()
