import logging
from typing import Optional, List, Dict, Any
from datetime import datetime

from services.kg.graph.neo4j_client import neo4j_client

logger = logging.getLogger(__name__)


class RelationRepository:
    def __init__(self):
        self.client = neo4j_client

    async def create_relation(
        self,
        relation_id: str,
        source_id: str,
        target_id: str,
        relation_type: str,
        properties: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        properties = properties or {}
        now = datetime.utcnow().isoformat()
        
        query = """
        MATCH (source:Entity {id: $source_id})
        MATCH (target:Entity {id: $target_id})
        MERGE (source)-[r:RELATES {id: $relation_id}]->(target)
        ON CREATE SET 
            r.type = $relation_type,
            r.created_at = $now,
            r.updated_at = $now
        ON MATCH SET
            r.type = $relation_type,
            r.updated_at = $now
        SET r += $properties
        RETURN source, r, target
        """
        
        params = {
            "relation_id": relation_id,
            "source_id": source_id,
            "target_id": target_id,
            "relation_type": relation_type,
            "now": now,
            "properties": properties
        }
        
        result = await self.client.execute_write(query, params)
        if result:
            return {
                "source": result[0].get("source", {}),
                "relation": result[0].get("r", {}),
                "target": result[0].get("target", {})
            }
        return {}

    async def update_relation(
        self,
        relation_id: str,
        properties: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        now = datetime.utcnow().isoformat()
        properties["updated_at"] = now
        
        query = """
        MATCH ()-[r:RELATES {id: $relation_id}]->()
        SET r += $properties
        RETURN r
        """
        
        params = {
            "relation_id": relation_id,
            "properties": properties
        }
        
        result = await self.client.execute_write(query, params)
        if result:
            return result[0].get("r", {})
        return None

    async def get_relation_by_id(self, relation_id: str) -> Optional[Dict[str, Any]]:
        query = """
        MATCH (source)-[r:RELATES {id: $relation_id}]->(target)
        RETURN source, r, target
        """
        
        result = await self.client.execute_read(query, {"relation_id": relation_id})
        if result:
            return {
                "source": result[0].get("source", {}),
                "relation": result[0].get("r", {}),
                "target": result[0].get("target", {})
            }
        return None

    async def get_relations_by_entity(
        self,
        entity_id: str,
        direction: str = "both",
        skip: int = 0,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        if direction == "outgoing":
            query = """
            MATCH (source:Entity {id: $entity_id})-[r:RELATES]->(target)
            RETURN source, r, target
            SKIP $skip
            LIMIT $limit
            """
        elif direction == "incoming":
            query = """
            MATCH (source)-[r:RELATES]->(target:Entity {id: $entity_id})
            RETURN source, r, target
            SKIP $skip
            LIMIT $limit
            """
        else:
            query = """
            MATCH (source)-[r:RELATES]-(target:Entity {id: $entity_id})
            RETURN source, r, target
            SKIP $skip
            LIMIT $limit
            """
        
        params = {
            "entity_id": entity_id,
            "skip": skip,
            "limit": limit
        }
        
        result = await self.client.execute_read(query, params)
        return [
            {
                "source": record.get("source", {}),
                "relation": record.get("r", {}),
                "target": record.get("target", {})
            }
            for record in result
        ]

    async def get_relations_by_type(
        self,
        relation_type: str,
        skip: int = 0,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        query = """
        MATCH (source)-[r:RELATES {type: $relation_type}]->(target)
        RETURN source, r, target
        SKIP $skip
        LIMIT $limit
        """
        
        params = {
            "relation_type": relation_type,
            "skip": skip,
            "limit": limit
        }
        
        result = await self.client.execute_read(query, params)
        return [
            {
                "source": record.get("source", {}),
                "relation": record.get("r", {}),
                "target": record.get("target", {})
            }
            for record in result
        ]

    async def delete_relation(self, relation_id: str) -> bool:
        query = """
        MATCH ()-[r:RELATES {id: $relation_id}]->()
        DELETE r
        RETURN count(r) as deleted
        """
        
        result = await self.client.execute_write(query, {"relation_id": relation_id})
        return len(result) > 0 and result[0].get("deleted", 0) > 0

    async def count_relations_by_entity(self, entity_id: str) -> int:
        query = """
        MATCH (:Entity {id: $entity_id})-[r:RELATES]-()
        RETURN count(r) as count
        """
        
        result = await self.client.execute_read(query, {"entity_id": entity_id})
        if result:
            return result[0].get("count", 0)
        return 0

    async def get_relations_by_head_entity(
        self,
        head_entity_id: str,
        skip: int = 0,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        query = """
        MATCH (source:Entity {id: $head_entity_id})-[r:RELATES]->(target)
        RETURN source.id as head_entity_id, 
               source.name as head_entity_name,
               r.id as id,
               r.type as relation_type,
               target.id as tail_entity_id,
               target.name as tail_entity_name,
               r.confidence as confidence
        SKIP $skip
        LIMIT $limit
        """
        
        params = {
            "head_entity_id": head_entity_id,
            "skip": skip,
            "limit": limit
        }
        
        result = await self.client.execute_read(query, params)
        return result

    async def get_relations_by_tail_entity(
        self,
        tail_entity_id: str,
        skip: int = 0,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        query = """
        MATCH (source)-[r:RELATES]->(target:Entity {id: $tail_entity_id})
        RETURN source.id as head_entity_id, 
               source.name as head_entity_name,
               r.id as id,
               r.type as relation_type,
               target.id as tail_entity_id,
               target.name as tail_entity_name,
               r.confidence as confidence
        SKIP $skip
        LIMIT $limit
        """
        
        params = {
            "tail_entity_id": tail_entity_id,
            "skip": skip,
            "limit": limit
        }
        
        result = await self.client.execute_read(query, params)
        return result


relation_repository = RelationRepository()
