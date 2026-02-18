import logging
import json
import hashlib
from typing import Optional, List, Dict, Any
from services.kg.graph.neo4j_client import neo4j_client
from services.kg.graph.entity_repository import entity_repository

logger = logging.getLogger(__name__)


class MultiHopQueryService:
    def __init__(self):
        self.client = neo4j_client
        self.entity_repo = entity_repository
        self._cache: Dict[str, Any] = {}

    async def query_2hop(
        self,
        start_entity_id: str,
        relation_types: Optional[List[str]] = None,
        entity_types: Optional[List[str]] = None,
        min_confidence: float = 0.0,
        limit: int = 100
    ) -> Dict[str, Any]:
        cache_key = self._generate_cache_key("2hop", start_entity_id, relation_types, entity_types, min_confidence)
        cached = await self._get_cached_result(cache_key)
        if cached:
            return cached

        query = """
        MATCH path = (start:Entity {id: $start_id})-[:RELATES*1..2]-(end:Entity)
        WHERE ($relation_types IS NULL OR ALL(r IN relationships(path) WHERE r.type IN $relation_types))
          AND ($entity_types IS NULL OR end.type IN $entity_types)
          AND ALL(r IN relationships(path) WHERE r.confidence >= $min_confidence)
        WITH path, end,
             [n IN nodes(path) | {id: n.id, name: n.name, type: n.type}] as node_list,
             [r IN relationships(path) | {id: r.id, type: r.type, confidence: r.confidence}] as rel_list
        RETURN DISTINCT 
            end.id as entity_id,
            end.name as entity_name,
            end.type as entity_type,
            node_list as path_nodes,
            rel_list as path_relations,
            length(path) as hop_count
        ORDER BY hop_count, end.name
        LIMIT $limit
        """

        params = {
            "start_id": start_entity_id,
            "relation_types": relation_types,
            "entity_types": entity_types,
            "min_confidence": min_confidence,
            "limit": limit
        }

        results = await self.client.execute_read(query, params)
        response = {
            "results": results,
            "total": len(results),
            "hops": 2,
            "start_entity_id": start_entity_id
        }

        await self.cache_result(cache_key, response)
        return response

    async def query_3hop(
        self,
        start_entity_id: str,
        relation_types: Optional[List[str]] = None,
        entity_types: Optional[List[str]] = None,
        min_confidence: float = 0.0,
        limit: int = 100
    ) -> Dict[str, Any]:
        cache_key = self._generate_cache_key("3hop", start_entity_id, relation_types, entity_types, min_confidence)
        cached = await self._get_cached_result(cache_key)
        if cached:
            return cached

        query = """
        MATCH path = (start:Entity {id: $start_id})-[:RELATES*1..3]-(end:Entity)
        WHERE ($relation_types IS NULL OR ALL(r IN relationships(path) WHERE r.type IN $relation_types))
          AND ($entity_types IS NULL OR end.type IN $entity_types)
          AND ALL(r IN relationships(path) WHERE r.confidence >= $min_confidence)
        WITH path, end,
             [n IN nodes(path) | {id: n.id, name: n.name, type: n.type}] as node_list,
             [r IN relationships(path) | {id: r.id, type: r.type, confidence: r.confidence}] as rel_list
        RETURN DISTINCT 
            end.id as entity_id,
            end.name as entity_name,
            end.type as entity_type,
            node_list as path_nodes,
            rel_list as path_relations,
            length(path) as hop_count
        ORDER BY hop_count, end.name
        LIMIT $limit
        """

        params = {
            "start_id": start_entity_id,
            "relation_types": relation_types,
            "entity_types": entity_types,
            "min_confidence": min_confidence,
            "limit": limit
        }

        results = await self.client.execute_read(query, params)
        response = {
            "results": results,
            "total": len(results),
            "hops": 3,
            "start_entity_id": start_entity_id
        }

        await self.cache_result(cache_key, response)
        return response

    async def query_4hop(
        self,
        start_entity_id: str,
        relation_types: Optional[List[str]] = None,
        entity_types: Optional[List[str]] = None,
        min_confidence: float = 0.0,
        limit: int = 100
    ) -> Dict[str, Any]:
        cache_key = self._generate_cache_key("4hop", start_entity_id, relation_types, entity_types, min_confidence)
        cached = await self._get_cached_result(cache_key)
        if cached:
            return cached

        query = """
        MATCH path = (start:Entity {id: $start_id})-[:RELATES*1..4]-(end:Entity)
        WHERE ($relation_types IS NULL OR ALL(r IN relationships(path) WHERE r.type IN $relation_types))
          AND ($entity_types IS NULL OR end.type IN $entity_types)
          AND ALL(r IN relationships(path) WHERE r.confidence >= $min_confidence)
        WITH path, end,
             [n IN nodes(path) | {id: n.id, name: n.name, type: n.type}] as node_list,
             [r IN relationships(path) | {id: r.id, type: r.type, confidence: r.confidence}] as rel_list
        RETURN DISTINCT 
            end.id as entity_id,
            end.name as entity_name,
            end.type as entity_type,
            node_list as path_nodes,
            rel_list as path_relations,
            length(path) as hop_count
        ORDER BY hop_count, end.name
        LIMIT $limit
        """

        params = {
            "start_id": start_entity_id,
            "relation_types": relation_types,
            "entity_types": entity_types,
            "min_confidence": min_confidence,
            "limit": limit
        }

        results = await self.client.execute_read(query, params)
        response = {
            "results": results,
            "total": len(results),
            "hops": 4,
            "start_entity_id": start_entity_id
        }

        await self.cache_result(cache_key, response)
        return response

    async def query_with_filters(
        self,
        start_entity_id: str,
        hops: int,
        relation_types: Optional[List[str]] = None,
        entity_types: Optional[List[str]] = None,
        min_confidence: float = 0.0,
        property_filters: Optional[Dict[str, Any]] = None,
        limit: int = 100
    ) -> Dict[str, Any]:
        if hops < 1 or hops > 4:
            raise ValueError("Hops must be between 1 and 4")

        cache_key = self._generate_cache_key(
            f"{hops}hop_filtered", 
            start_entity_id, 
            relation_types, 
            entity_types, 
            min_confidence,
            property_filters
        )
        cached = await self._get_cached_result(cache_key)
        if cached:
            return cached

        where_clauses = [
            "($relation_types IS NULL OR ALL(r IN relationships(path) WHERE r.type IN $relation_types))",
            "($entity_types IS NULL OR end.type IN $entity_types)",
            "ALL(r IN relationships(path) WHERE r.confidence >= $min_confidence)"
        ]

        if property_filters:
            for key, value in property_filters.items():
                where_clauses.append(f"end.{key} = ${key}")

        where_clause = " AND ".join(where_clauses)

        query = f"""
        MATCH path = (start:Entity {{id: $start_id}})-[:RELATES*1..{hops}]-(end:Entity)
        WHERE {where_clause}
        WITH path, end,
             [n IN nodes(path) | {{id: n.id, name: n.name, type: n.type}}] as node_list,
             [r IN relationships(path) | {{id: r.id, type: r.type, confidence: r.confidence}}] as rel_list
        RETURN DISTINCT 
            end.id as entity_id,
            end.name as entity_name,
            end.type as entity_type,
            node_list as path_nodes,
            rel_list as path_relations,
            length(path) as hop_count
        ORDER BY hop_count, end.name
        LIMIT $limit
        """

        params = {
            "start_id": start_entity_id,
            "relation_types": relation_types,
            "entity_types": entity_types,
            "min_confidence": min_confidence,
            "limit": limit
        }

        if property_filters:
            params.update(property_filters)

        results = await self.client.execute_read(query, params)
        response = {
            "results": results,
            "total": len(results),
            "hops": hops,
            "start_entity_id": start_entity_id,
            "filters_applied": {
                "relation_types": relation_types,
                "entity_types": entity_types,
                "min_confidence": min_confidence,
                "property_filters": property_filters
            }
        }

        await self.cache_result(cache_key, response)
        return response

    async def cache_result(self, key: str, result: Dict[str, Any], ttl: int = 300) -> bool:
        try:
            self._cache[key] = {
                "data": result,
                "ttl": ttl
            }
            logger.debug(f"Cached result for key: {key}")
            return True
        except Exception as e:
            logger.error(f"Failed to cache result: {e}")
            return False

    async def _get_cached_result(self, key: str) -> Optional[Dict[str, Any]]:
        try:
            cached = self._cache.get(key)
            if cached:
                logger.debug(f"Cache hit for key: {key}")
                return cached.get("data")
            return None
        except Exception as e:
            logger.error(f"Failed to get cached result: {e}")
            return None

    def _generate_cache_key(
        self,
        prefix: str,
        entity_id: str,
        relation_types: Optional[List[str]],
        entity_types: Optional[List[str]],
        min_confidence: float,
        extra: Optional[Dict[str, Any]] = None
    ) -> str:
        key_data = {
            "prefix": prefix,
            "entity_id": entity_id,
            "relation_types": sorted(relation_types) if relation_types else None,
            "entity_types": sorted(entity_types) if entity_types else None,
            "min_confidence": min_confidence,
            "extra": extra
        }
        key_string = json.dumps(key_data, sort_keys=True)
        return hashlib.md5(key_string.encode()).hexdigest()

    def clear_cache(self) -> None:
        self._cache.clear()
        logger.info("Multi-hop query cache cleared")


multi_hop_query_service = MultiHopQueryService()
