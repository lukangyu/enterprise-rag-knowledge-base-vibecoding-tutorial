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
class Relation:
    head: str
    relation: str
    tail: str
    evidence: str
    confidence: float = 1.0
    properties: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "head": self.head,
            "relation": self.relation,
            "tail": self.tail,
            "evidence": self.evidence,
            "confidence": self.confidence,
            "properties": self.properties or {}
        }


RELATION_EXTRACTION_PROMPT = """请从以下文本中抽取实体之间的关系：

文本：{text}

已识别实体：
{entities}

关系类型：
{relation_types}

要求：
1. 只抽取文本中明确表达的关系
2. 确保头实体和尾实体都在已识别实体列表中
3. 为每个关系提供原文证据
4. 不要推断隐含的关系

输出格式（JSON）：
{{
    "relations": [
        {{
            "head": "头实体",
            "relation": "关系类型",
            "tail": "尾实体",
            "evidence": "原文证据"
        }}
    ]
}}

请直接输出JSON，不要包含其他内容。"""


class LLMRelationExtractor:
    def __init__(self):
        self.api_url = kg_settings.DASHSCOPE_API_URL
        self.api_key = kg_settings.DASHSCOPE_API_KEY
        self.model = kg_settings.QWEN_MODEL
        self.relation_types = kg_settings.RELATION_TYPES
        self.max_tokens = kg_settings.MAX_TOKENS
        self.timeout = kg_settings.REQUEST_TIMEOUT

    def _build_relation_types_str(self) -> str:
        lines = []
        for type_code, type_name in self.relation_types.items():
            lines.append(f"- {type_code}: {type_name}")
        return "\n".join(lines)

    def _build_entities_str(self, entities: List[Any]) -> str:
        entity_lines = []
        for entity in entities:
            if hasattr(entity, 'name') and hasattr(entity, 'type'):
                entity_lines.append(f"- {entity.name} ({entity.type})")
            elif isinstance(entity, dict):
                name = entity.get('name', '')
                etype = entity.get('type', '')
                entity_lines.append(f"- {name} ({etype})")
        return "\n".join(entity_lines)

    def _build_prompt(self, text: str, entities: List[Any]) -> str:
        relation_types_str = self._build_relation_types_str()
        entities_str = self._build_entities_str(entities)
        return RELATION_EXTRACTION_PROMPT.format(
            text=text,
            entities=entities_str,
            relation_types=relation_types_str
        )

    def _parse_response(self, response_text: str) -> List[Relation]:
        try:
            json_match = re.search(r'\{[\s\S]*\}', response_text)
            if json_match:
                json_str = json_match.group()
                data = json.loads(json_str)
                relations = []
                for item in data.get("relations", []):
                    relation = Relation(
                        head=item.get("head", ""),
                        relation=item.get("relation", ""),
                        tail=item.get("tail", ""),
                        evidence=item.get("evidence", ""),
                        confidence=item.get("confidence", 1.0),
                        properties=item.get("properties")
                    )
                    if relation.head and relation.relation and relation.tail:
                        relations.append(relation)
                return relations
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
                        {"role": "system", "content": "你是一个专业的关系抽取助手，擅长从文本中识别实体之间的关系。"},
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

    async def extract(
        self,
        text: str,
        entities: List[Any]
    ) -> List[Relation]:
        if not text or not text.strip():
            return []

        if not entities:
            return []

        prompt = self._build_prompt(text, entities)
        try:
            response_text = await self._call_llm(prompt)
            relations = self._parse_response(response_text)
            logger.info(f"从文本中抽取了 {len(relations)} 个关系")
            return relations
        except Exception as e:
            logger.error(f"关系抽取失败: {e}")
            return []

    async def batch_extract(
        self,
        texts: List[str],
        entities_list: List[List[Any]],
        batch_size: int = None
    ) -> List[List[Relation]]:
        if len(texts) != len(entities_list):
            raise ValueError("文本列表和实体列表长度不匹配")

        if batch_size is None:
            batch_size = kg_settings.BATCH_SIZE

        all_relations = []
        for i in range(0, len(texts), batch_size):
            batch_texts = texts[i:i + batch_size]
            batch_entities = entities_list[i:i + batch_size]

            for text, entities in zip(batch_texts, batch_entities):
                relations = await self.extract(text, entities)
                all_relations.append(relations)

            logger.info(f"已完成 {min(i + batch_size, len(texts))}/{len(texts)} 个文本的关系抽取")

        return all_relations

    async def extract_with_custom_types(
        self,
        text: str,
        entities: List[Any],
        custom_relation_types: Dict[str, str]
    ) -> List[Relation]:
        original_types = self.relation_types
        self.relation_types = custom_relation_types
        try:
            return await self.extract(text, entities)
        finally:
            self.relation_types = original_types
