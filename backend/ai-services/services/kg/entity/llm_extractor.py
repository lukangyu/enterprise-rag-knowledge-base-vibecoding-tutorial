import httpx
import json
import logging
import re
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from tenacity import retry, stop_after_attempt, wait_exponential

from config.kg_settings import kg_settings

logger = logging.getLogger(__name__)


@dataclass
class Entity:
    name: str
    type: str
    description: str
    confidence: float = 1.0
    properties: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "type": self.type,
            "description": self.description,
            "confidence": self.confidence,
            "properties": self.properties or {}
        }


ENTITY_EXTRACTION_PROMPT = """请从以下文本中抽取实体，按类型分类：

文本：{text}

实体类型：
{entity_types}

要求：
1. 识别文本中所有重要的实体
2. 为每个实体提供简短描述
3. 确保实体名称准确，不要添加原文中不存在的信息

输出格式（JSON）：
{{
    "entities": [
        {{"name": "实体名", "type": "类型", "description": "描述"}}
    ]
}}

请直接输出JSON，不要包含其他内容。"""


class LLMEntityExtractor:
    def __init__(self):
        self.api_url = kg_settings.DASHSCOPE_API_URL
        self.api_key = kg_settings.DASHSCOPE_API_KEY
        self.model = kg_settings.QWEN_MODEL
        self.entity_types = kg_settings.ENTITY_TYPES
        self.max_tokens = kg_settings.MAX_TOKENS
        self.timeout = kg_settings.REQUEST_TIMEOUT

    def _build_entity_types_str(self) -> str:
        lines = []
        for type_code, type_name in self.entity_types.items():
            lines.append(f"- {type_code}: {type_name}")
        return "\n".join(lines)

    def _build_prompt(self, text: str) -> str:
        entity_types_str = self._build_entity_types_str()
        return ENTITY_EXTRACTION_PROMPT.format(
            text=text,
            entity_types=entity_types_str
        )

    def _parse_response(self, response_text: str) -> List[Entity]:
        try:
            json_match = re.search(r'\{[\s\S]*\}', response_text)
            if json_match:
                json_str = json_match.group()
                data = json.loads(json_str)
                entities = []
                for item in data.get("entities", []):
                    entity = Entity(
                        name=item.get("name", ""),
                        type=item.get("type", ""),
                        description=item.get("description", ""),
                        confidence=item.get("confidence", 1.0),
                        properties=item.get("properties")
                    )
                    if entity.name and entity.type:
                        entities.append(entity)
                return entities
            return []
        except json.JSONDecodeError as e:
            logger.error(f"JSON解析失败: {e}")
            return []

    @retry(
        stop=stop_after_attempt(kg_settings.MAX_RETRY_ATTEMPTS),
        wait=wait_exponential(
            multiplier=1,
            min=kg_settings.RETRY_MIN_WAIT,
            max=kg_settings.RETRY_MAX_WAIT
        )
    )
    async def _call_llm(self, prompt: str) -> str:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.api_url,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": self.model,
                    "messages": [
                        {"role": "system", "content": "你是一个专业的实体抽取助手，擅长从文本中识别和提取实体信息。"},
                        {"role": "user", "content": prompt}
                    ],
                    "max_tokens": self.max_tokens,
                    "temperature": 0.1
                },
                timeout=self.timeout
            )
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"]

    async def extract(self, text: str) -> List[Entity]:
        if not text or not text.strip():
            return []

        prompt = self._build_prompt(text)
        try:
            response_text = await self._call_llm(prompt)
            entities = self._parse_response(response_text)
            logger.info(f"从文本中抽取了 {len(entities)} 个实体")
            return entities
        except Exception as e:
            logger.error(f"实体抽取失败: {e}")
            return []

    async def batch_extract(
        self,
        texts: List[str],
        batch_size: int = None
    ) -> List[List[Entity]]:
        if batch_size is None:
            batch_size = kg_settings.BATCH_SIZE

        all_entities = []
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            batch_entities = []
            for text in batch:
                entities = await self.extract(text)
                batch_entities.append(entities)
            all_entities.extend(batch_entities)
            logger.info(f"已完成 {min(i + batch_size, len(texts))}/{len(texts)} 个文本的实体抽取")

        return all_entities

    async def extract_with_custom_types(
        self,
        text: str,
        custom_entity_types: Dict[str, str]
    ) -> List[Entity]:
        original_types = self.entity_types
        self.entity_types = custom_entity_types
        try:
            return await self.extract(text)
        finally:
            self.entity_types = original_types
