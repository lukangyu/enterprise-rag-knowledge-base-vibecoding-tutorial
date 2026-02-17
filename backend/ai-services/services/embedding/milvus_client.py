from pymilvus import (
    connections, Collection, FieldSchema, CollectionSchema,
    DataType, utility
)
import logging
from typing import List, Dict, Any, Optional
import uuid

from config.settings import settings

logger = logging.getLogger(__name__)


class MilvusClient:
    def __init__(self):
        self.collection_name = settings.MILVUS_COLLECTION
        self.dimension = settings.EMBEDDING_DIMENSION
        self._collection: Optional[Collection] = None

    def connect(self):
        connections.connect(
            alias="default",
            host=settings.MILVUS_HOST,
            port=settings.MILVUS_PORT
        )
        logger.info(f"Connected to Milvus at {settings.MILVUS_HOST}:{settings.MILVUS_PORT}")

    def create_collection(self):
        """创建向量集合"""
        if utility.has_collection(self.collection_name):
            logger.info(f"Collection {self.collection_name} already exists")
            return

        fields = [
            FieldSchema(name="id", dtype=DataType.VARCHAR, max_length=64, is_primary=True),
            FieldSchema(name="doc_id", dtype=DataType.VARCHAR, max_length=64),
            FieldSchema(name="chunk_id", dtype=DataType.VARCHAR, max_length=64),
            FieldSchema(name="content", dtype=DataType.VARCHAR, max_length=65535),
            FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=self.dimension)
        ]

        schema = CollectionSchema(fields=fields, description="Document vectors")
        collection = Collection(name=self.collection_name, schema=schema)

        index_params = {
            "metric_type": "COSINE",
            "index_type": "IVF_FLAT",
            "params": {"nlist": 1024}
        }
        collection.create_index(field_name="embedding", index_params=index_params)
        logger.info(f"Created collection {self.collection_name} with index")

    def get_collection(self) -> Collection:
        if self._collection is None:
            self._collection = Collection(self.collection_name)
        return self._collection

    def insert(self, vectors: List[Dict[str, Any]]) -> List[str]:
        """插入向量"""
        collection = self.get_collection()

        ids = [str(uuid.uuid4()) for _ in vectors]
        data = [
            ids,
            [v["doc_id"] for v in vectors],
            [v["chunk_id"] for v in vectors],
            [v["content"] for v in vectors],
            [v["embedding"] for v in vectors]
        ]

        collection.insert(data)
        collection.flush()
        return ids

    def search(
        self,
        query_vector: List[float],
        top_k: int = 10,
        doc_ids: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """搜索相似向量"""
        collection = self.get_collection()
        collection.load()

        search_params = {"metric_type": "COSINE", "params": {"nprobe": 10}}

        expr = None
        if doc_ids:
            expr = f'doc_id in {doc_ids}'

        results = collection.search(
            data=[query_vector],
            anns_field="embedding",
            param=search_params,
            limit=top_k,
            expr=expr,
            output_fields=["doc_id", "chunk_id", "content"]
        )

        hits = []
        for hit in results[0]:
            hits.append({
                "id": hit.id,
                "score": hit.score,
                "doc_id": hit.entity.get("doc_id"),
                "chunk_id": hit.entity.get("chunk_id"),
                "content": hit.entity.get("content")
            })

        return hits

    def delete_by_doc_id(self, doc_id: str):
        """删除文档的所有向量"""
        collection = self.get_collection()
        expr = f'doc_id == "{doc_id}"'
        collection.delete(expr)
        collection.flush()


milvus_client = MilvusClient()
