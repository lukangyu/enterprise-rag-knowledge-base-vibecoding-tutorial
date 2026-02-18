import logging
from typing import Optional, List, Dict, Any
from datetime import datetime

from services.kg.graph.neo4j_client import neo4j_client

logger = logging.getLogger(__name__)


class EntityRepository:
    def __init__(self):
        self.client = neo4j_client

    async def create_entity(
        self,
        entity_id: str,
        name: str,
        entity_type: str,
        properties: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        properties = properties or {}
        now = datetime.utcnow().isoformat()
        
        query = """
        MERGE (e:Entity {id: $entity_id})
        ON CREATE SET 
            e.name = $name,
            e.type = $entity_type,
            e.created_at = $now,
            e.updated_at = $now
        ON MATCH SET
            e.name = $name,
            e.type = $entity_type,
            e.updated_at = $now
        SET e += $properties
        RETURN e
        """
        
        params = {
            "entity_id": entity_id,
            "name": name,
            "entity_type": entity_type,
            "now": now,
            "properties": properties
        }
        
        result = await self.client.execute_write(query, params)
        if result:
            return result[0].get("e", {})
        return {}

    async def update_entity(
        self,
        entity_id: str,
        properties: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        now = datetime.utcnow().isoformat()
        properties["updated_at"] = now
        
        query = """
        MATCH (e:Entity {id: $entity_id})
        SET e += $properties
        RETURN e
        """
        
        params = {
            "entity_id": entity_id,
            "properties": properties
        }
        
        result = await self.client.execute_write(query, params)
        if result:
            return result[0].get("e", {})
        return None

    async def get_entity_by_id(self, entity_id: str) -> Optional[Dict[str, Any]]:
        query = """
        MATCH (e:Entity {id: $entity_id})
        RETURN e
        """
        
        result = await self.client.execute_read(query, {"entity_id": entity_id})
        if result:
            return result[0].get("e", {})
        return None

    async def get_entity_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        query = """
        MATCH (e:Entity {name: $name})
        RETURN e
        """
        
        result = await self.client.execute_read(query, {"name": name})
        if result:
            return result[0].get("e", {})
        return None

    async def get_entities_by_type(
        self,
        entity_type: str,
        skip: int = 0,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        query = """
        MATCH (e:Entity {type: $entity_type})
        RETURN e
        ORDER BY e.created_at DESC
        SKIP $skip
        LIMIT $limit
        """
        
        params = {
            "entity_type": entity_type,
            "skip": skip,
            "limit": limit
        }
        
        result = await self.client.execute_read(query, params)
        return [record.get("e", {}) for record in result]

    async def delete_entity(self, entity_id: str) -> bool:
        query = """
        MATCH (e:Entity {id: $entity_id})
        DETACH DELETE e
        RETURN count(e) as deleted
        """
        
        result = await self.client.execute_write(query, {"entity_id": entity_id})
        return len(result) > 0 and result[0].get("deleted", 0) > 0

    async def search_entities(
        self,
        keyword: str,
        entity_type: Optional[str] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        if entity_type:
            query = """
            CALL db.index.fulltext.queryNodes('entity_fulltext', $keyword) 
            YIELD node as e
            WHERE e.type = $entity_type
            RETURN e
            SKIP $skip
            LIMIT $limit
            """
        else:
            query = """
            CALL db.index.fulltext.queryNodes('entity_fulltext', $keyword) 
            YIELD node as e
            RETURN e
            SKIP $skip
            LIMIT $limit
            """
        
        params = {
            "keyword": keyword,
            "entity_type": entity_type,
            "skip": skip,
            "limit": limit
        }
        
        result = await self.client.execute_read(query, params)
        return [record.get("e", {}) for record in result]

    async def count_entities_by_type(self, entity_type: str) -> int:
        query = """
        MATCH (e:Entity {type: $entity_type})
        RETURN count(e) as count
        """
        
        result = await self.client.execute_read(query, {"entity_type": entity_type})
        if result:
            return result[0].get("count", 0)
        return 0


entity_repository = EntityRepository()
