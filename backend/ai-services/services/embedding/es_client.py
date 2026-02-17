from elasticsearch import Elasticsearch
from elasticsearch.helpers import bulk
from typing import List, Dict, Optional, Any
import logging
from config.settings import settings

logger = logging.getLogger(__name__)


class ElasticsearchClient:
    def __init__(self):
        hosts = [f"{settings.ES_SCHEME}://{settings.ES_HOST}:{settings.ES_PORT}"]
        
        if settings.ES_USERNAME and settings.ES_PASSWORD:
            self.client = Elasticsearch(
                hosts,
                basic_auth=(settings.ES_USERNAME, settings.ES_PASSWORD)
            )
        else:
            self.client = Elasticsearch(hosts)
        
        self.index = settings.ES_INDEX
        logger.info(f"Elasticsearch client initialized: {hosts}")

    def create_index(self, index_name: Optional[str] = None) -> bool:
        index = index_name or self.index
        
        if self.client.indices.exists(index=index):
            logger.info(f"Index {index} already exists")
            return True
        
        settings_body = {
            "number_of_shards": 3,
            "number_of_replicas": 1,
            "analysis": {
                "analyzer": {
                    "ik_smart_analyzer": {
                        "type": "custom",
                        "tokenizer": "ik_smart"
                    },
                    "ik_max_word_analyzer": {
                        "type": "custom",
                        "tokenizer": "ik_max_word"
                    }
                }
            }
        }
        
        mappings = {
            "properties": {
                "doc_id": {"type": "keyword"},
                "chunk_id": {"type": "keyword"},
                "content": {
                    "type": "text",
                    "analyzer": "ik_max_word_analyzer",
                    "search_analyzer": "ik_smart_analyzer"
                },
                "title": {
                    "type": "text",
                    "analyzer": "ik_max_word_analyzer"
                },
                "keywords": {"type": "keyword"},
                "metadata": {
                    "properties": {
                        "doc_type": {"type": "keyword"},
                        "category": {"type": "keyword"},
                        "tags": {"type": "keyword"},
                        "created_at": {"type": "date"}
                    }
                },
                "milvus_id": {"type": "keyword"}
            }
        }
        
        response = self.client.indices.create(
            index=index,
            settings=settings_body,
            mappings=mappings
        )
        
        logger.info(f"Created index {index}: {response}")
        return response.get("acknowledged", False)

    def index_document(
        self,
        doc_id: str,
        chunk_id: str,
        content: str,
        title: Optional[str] = None,
        keywords: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        milvus_id: Optional[str] = None,
        index_name: Optional[str] = None
    ) -> Dict[str, Any]:
        index = index_name or self.index
        
        document = {
            "doc_id": doc_id,
            "chunk_id": chunk_id,
            "content": content,
            "title": title or "",
            "keywords": keywords or [],
            "metadata": metadata or {},
            "milvus_id": milvus_id or ""
        }
        
        id_ = f"{doc_id}_{chunk_id}"
        response = self.client.index(index=index, id=id_, document=document)
        
        logger.debug(f"Indexed document {id_} in {index}")
        return response

    def bulk_index(
        self,
        documents: List[Dict[str, Any]],
        index_name: Optional[str] = None
    ) -> int:
        index = index_name or self.index
        
        actions = []
        for doc in documents:
            doc_id = doc.get("doc_id", "")
            chunk_id = doc.get("chunk_id", "")
            id_ = f"{doc_id}_{chunk_id}"
            
            actions.append({
                "_index": index,
                "_id": id_,
                "_source": doc
            })
        
        success, failed = bulk(self.client, actions)
        logger.info(f"Bulk indexed {success} documents, {len(failed)} failed")
        return success

    def search(
        self,
        query: str,
        top_k: int = 100,
        filters: Optional[Dict[str, Any]] = None,
        index_name: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        index = index_name or self.index
        
        search_body = {
            "query": {
                "bool": {
                    "must": [
                        {
                            "multi_match": {
                                "query": query,
                                "fields": ["content", "title", "keywords"]
                            }
                        }
                    ]
                }
            },
            "size": top_k
        }
        
        if filters:
            filter_clauses = []
            for key, value in filters.items():
                if isinstance(value, list):
                    filter_clauses.append({"terms": {key: value}})
                else:
                    filter_clauses.append({"term": {key: value}})
            
            search_body["query"]["bool"]["filter"] = filter_clauses
        
        response = self.client.search(index=index, body=search_body)
        
        results = []
        for hit in response["hits"]["hits"]:
            result = hit["_source"]
            result["_id"] = hit["_id"]
            result["_score"] = hit["_score"]
            results.append(result)
        
        logger.debug(f"Search returned {len(results)} results for query: {query[:50]}...")
        return results

    def delete_document(self, doc_id: str, index_name: Optional[str] = None) -> bool:
        index = index_name or self.index
        
        query = {
            "query": {
                "term": {"doc_id": doc_id}
            }
        }
        
        response = self.client.delete_by_query(index=index, body=query)
        deleted = response.get("deleted", 0)
        
        logger.info(f"Deleted {deleted} documents with doc_id: {doc_id}")
        return deleted > 0

    def get_document(self, doc_id: str, chunk_id: str, index_name: Optional[str] = None) -> Optional[Dict[str, Any]]:
        index = index_name or self.index
        id_ = f"{doc_id}_{chunk_id}"
        
        try:
            response = self.client.get(index=index, id=id_)
            result = response["_source"]
            result["_id"] = response["_id"]
            return result
        except Exception as e:
            logger.warning(f"Document {id_} not found: {e}")
            return None

    def count(self, index_name: Optional[str] = None) -> int:
        index = index_name or self.index
        response = self.client.count(index=index)
        return response["count"]

    def health_check(self) -> Dict[str, Any]:
        return self.client.cluster.health()


es_client = ElasticsearchClient()
