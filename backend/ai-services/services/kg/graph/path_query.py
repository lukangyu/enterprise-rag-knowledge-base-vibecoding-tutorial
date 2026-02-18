import logging
from typing import Optional, List, Dict, Any
from services.kg.graph.neo4j_client import neo4j_client
from services.kg.graph.entity_repository import entity_repository

logger = logging.getLogger(__name__)


class PathQueryService:
    def __init__(self):
        self.client = neo4j_client
        self.entity_repo = entity_repository

    async def find_shortest_path(
        self,
        source_entity: str,
        target_entity: str,
        relation_types: Optional[List[str]] = None,
        min_confidence: float = 0.0,
        max_hops: int = 10
    ) -> Optional[Dict[str, Any]]:
        source = await self.entity_repo.get_entity_by_name(source_entity)
        if not source:
            source = await self.entity_repo.get_entity_by_id(source_entity)
        
        target = await self.entity_repo.get_entity_by_name(target_entity)
        if not target:
            target = await self.entity_repo.get_entity_by_id(target_entity)

        if not source or not target:
            return None

        source_id = source.get("id")
        target_id = target.get("id")

        query = """
        MATCH (source:Entity {id: $source_id}), (target:Entity {id: $target_id})
        CALL apoc.algo.shortestPath(source, target, 'RELATES', {
            relationshipQuery: $rel_query,
            minConfidence: $min_confidence
        })
        YIELD path
        WHERE ($relation_types IS NULL OR ALL(r IN relationships(path) WHERE r.type IN $relation_types))
          AND ALL(r IN relationships(path) WHERE r.confidence >= $min_confidence)
        RETURN 
            [n IN nodes(path) | {id: n.id, name: n.name, type: n.type}] as nodes,
            [r IN relationships(path) | {id: r.id, type: r.type, confidence: r.confidence}] as relations,
            length(path) as path_length
        """

        params = {
            "source_id": source_id,
            "target_id": target_id,
            "relation_types": relation_types,
            "min_confidence": min_confidence,
            "rel_query": "RELATES"
        }

        try:
            results = await self.client.execute_read(query, params)
            if results:
                result = results[0]
                return {
                    "path": {
                        "nodes": result.get("nodes", []),
                        "edges": result.get("relations", []),
                        "length": result.get("path_length", 0)
                    },
                    "confidence": await self.calculate_path_confidence(result.get("relations", [])),
                    "source_entity": source_entity,
                    "target_entity": target_entity
                }
        except Exception as e:
            logger.warning(f"APOC not available, using fallback: {e}")

        return await self._find_shortest_path_fallback(
            source_id, target_id, relation_types, min_confidence, max_hops
        )

    async def _find_shortest_path_fallback(
        self,
        source_id: str,
        target_id: str,
        relation_types: Optional[List[str]],
        min_confidence: float,
        max_hops: int
    ) -> Optional[Dict[str, Any]]:
        query = """
        MATCH path = (source:Entity {id: $source_id})-[:RELATES*1..%d]-(target:Entity {id: $target_id})
        WHERE ($relation_types IS NULL OR ALL(r IN relationships(path) WHERE r.type IN $relation_types))
          AND ALL(r IN relationships(path) WHERE r.confidence >= $min_confidence)
        WITH path,
             [n IN nodes(path) | {id: n.id, name: n.name, type: n.type}] as node_list,
             [r IN relationships(path) | {id: r.id, type: r.type, confidence: r.confidence}] as rel_list
        RETURN node_list as nodes, rel_list as relations, length(path) as path_length
        ORDER BY path_length
        LIMIT 1
        """ % max_hops

        params = {
            "source_id": source_id,
            "target_id": target_id,
            "relation_types": relation_types,
            "min_confidence": min_confidence
        }

        results = await self.client.execute_read(query, params)
        if results:
            result = results[0]
            return {
                "path": {
                    "nodes": result.get("nodes", []),
                    "edges": result.get("relations", []),
                    "length": result.get("path_length", 0)
                },
                "confidence": await self.calculate_path_confidence(result.get("relations", [])),
                "source_id": source_id,
                "target_id": target_id
            }
        return None

    async def find_all_paths(
        self,
        source_entity: str,
        target_entity: str,
        relation_types: Optional[List[str]] = None,
        min_confidence: float = 0.0,
        max_hops: int = 5,
        limit: int = 10
    ) -> Dict[str, Any]:
        source = await self.entity_repo.get_entity_by_name(source_entity)
        if not source:
            source = await self.entity_repo.get_entity_by_id(source_entity)
        
        target = await self.entity_repo.get_entity_by_name(target_entity)
        if not target:
            target = await self.entity_repo.get_entity_by_id(target_entity)

        if not source or not target:
            return {"paths": [], "total": 0}

        source_id = source.get("id")
        target_id = target.get("id")

        query = """
        MATCH path = (source:Entity {id: $source_id})-[:RELATES*1..%d]-(target:Entity {id: $target_id})
        WHERE ($relation_types IS NULL OR ALL(r IN relationships(path) WHERE r.type IN $relation_types))
          AND ALL(r IN relationships(path) WHERE r.confidence >= $min_confidence)
        WITH path,
             [n IN nodes(path) | {id: n.id, name: n.name, type: n.type}] as node_list,
             [r IN relationships(path) | {id: r.id, type: r.type, confidence: r.confidence}] as rel_list
        RETURN node_list as nodes, rel_list as relations, length(path) as path_length
        ORDER BY path_length
        LIMIT $limit
        """ % max_hops

        params = {
            "source_id": source_id,
            "target_id": target_id,
            "relation_types": relation_types,
            "min_confidence": min_confidence,
            "limit": limit
        }

        results = await self.client.execute_read(query, params)
        
        paths = []
        for result in results:
            path_data = {
                "nodes": result.get("nodes", []),
                "edges": result.get("relations", []),
                "length": result.get("path_length", 0),
                "confidence": await self.calculate_path_confidence(result.get("relations", []))
            }
            paths.append(path_data)

        return {
            "paths": paths,
            "total": len(paths),
            "source_entity": source_entity,
            "target_entity": target_entity
        }

    async def find_paths_with_hops(
        self,
        source_entity: str,
        target_entity: str,
        exact_hops: int,
        relation_types: Optional[List[str]] = None,
        min_confidence: float = 0.0,
        limit: int = 10
    ) -> Dict[str, Any]:
        if exact_hops < 1 or exact_hops > 10:
            raise ValueError("Hops must be between 1 and 10")

        source = await self.entity_repo.get_entity_by_name(source_entity)
        if not source:
            source = await self.entity_repo.get_entity_by_id(source_entity)
        
        target = await self.entity_repo.get_entity_by_name(target_entity)
        if not target:
            target = await self.entity_repo.get_entity_by_id(target_entity)

        if not source or not target:
            return {"paths": [], "total": 0}

        source_id = source.get("id")
        target_id = target.get("id")

        query = """
        MATCH path = (source:Entity {id: $source_id})-[:RELATES*%d]-(target:Entity {id: $target_id})
        WHERE ($relation_types IS NULL OR ALL(r IN relationships(path) WHERE r.type IN $relation_types))
          AND ALL(r IN relationships(path) WHERE r.confidence >= $min_confidence)
        WITH path,
             [n IN nodes(path) | {id: n.id, name: n.name, type: n.type}] as node_list,
             [r IN relationships(path) | {id: r.id, type: r.type, confidence: r.confidence}] as rel_list
        RETURN node_list as nodes, rel_list as relations, length(path) as path_length
        LIMIT $limit
        """ % exact_hops

        params = {
            "source_id": source_id,
            "target_id": target_id,
            "relation_types": relation_types,
            "min_confidence": min_confidence,
            "limit": limit
        }

        results = await self.client.execute_read(query, params)
        
        paths = []
        for result in results:
            path_data = {
                "nodes": result.get("nodes", []),
                "edges": result.get("relations", []),
                "length": result.get("path_length", 0),
                "confidence": await self.calculate_path_confidence(result.get("relations", []))
            }
            paths.append(path_data)

        return {
            "paths": paths,
            "total": len(paths),
            "exact_hops": exact_hops,
            "source_entity": source_entity,
            "target_entity": target_entity
        }

    async def calculate_path_confidence(self, relations: List[Dict[str, Any]]) -> float:
        if not relations:
            return 0.0

        confidences = [r.get("confidence", 1.0) for r in relations]
        
        product = 1.0
        for conf in confidences:
            product *= conf
        
        geometric_mean = product ** (1.0 / len(confidences))
        
        return round(geometric_mean, 4)


path_query_service = PathQueryService()
