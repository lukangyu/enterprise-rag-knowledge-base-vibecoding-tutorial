import httpx
import logging
from typing import List
from tenacity import retry, stop_after_attempt, wait_exponential

from config.settings import settings

logger = logging.getLogger(__name__)


class QwenEmbedding:
    def __init__(self):
        self.api_url = settings.QWEN_API_URL
        self.api_key = settings.QWEN_API_KEY
        self.model = settings.QWEN_MODEL
        self.dimension = settings.EMBEDDING_DIMENSION

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    async def embed(self, text: str) -> List[float]:
        """生成单个文本的向量"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.api_url,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": self.model,
                    "input": {"texts": [text]},
                    "parameters": {"text_type": "document"}
                },
                timeout=30.0
            )
            response.raise_for_status()
            data = response.json()
            return data["output"]["embeddings"][0]["embedding"]

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    async def embed_batch(self, texts: List[str], batch_size: int = 10) -> List[List[float]]:
        """批量生成向量"""
        all_embeddings = []

        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.api_url,
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": self.model,
                        "input": {"texts": batch},
                        "parameters": {"text_type": "document"}
                    },
                    timeout=60.0
                )
                response.raise_for_status()
                data = response.json()
                embeddings = [item["embedding"] for item in data["output"]["embeddings"]]
                all_embeddings.extend(embeddings)

        return all_embeddings
