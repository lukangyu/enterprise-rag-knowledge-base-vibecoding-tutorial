import logging
from typing import List, Dict, Any

from services.kg.graph.neo4j_client import neo4j_client

logger = logging.getLogger(__name__)


class IndexManager:
    def __init__(self):
        self.client = neo4j_client

    async def create_entity_name_index(self) -> bool:
        query = """
        CREATE INDEX entity_name_index IF NOT EXISTS
        FOR (e:Entity)
        ON (e.name)
        """
        
        try:
            await self.client.execute_write(query)
            logger.info("Created entity_name_index")
            return True
        except Exception as e:
            logger.error(f"Failed to create entity_name_index: {e}")
            return False

    async def create_entity_type_index(self) -> bool:
        query = """
        CREATE INDEX entity_type_index IF NOT EXISTS
        FOR (e:Entity)
        ON (e.type)
        """
        
        try:
            await self.client.execute_write(query)
            logger.info("Created entity_type_index")
            return True
        except Exception as e:
            logger.error(f"Failed to create entity_type_index: {e}")
            return False

    async def create_entity_id_index(self) -> bool:
        query = """
        CREATE INDEX entity_id_index IF NOT EXISTS
        FOR (e:Entity)
        ON (e.id)
        """
        
        try:
            await self.client.execute_write(query)
            logger.info("Created entity_id_index")
            return True
        except Exception as e:
            logger.error(f"Failed to create entity_id_index: {e}")
            return False

    async def create_fulltext_index(self) -> bool:
        query = """
        CREATE FULLTEXT INDEX entity_fulltext IF NOT EXISTS
        FOR (e:Entity)
        ON EACH [e.name, e.description]
        """
        
        try:
            await self.client.execute_write(query)
            logger.info("Created entity_fulltext index")
            return True
        except Exception as e:
            logger.error(f"Failed to create entity_fulltext index: {e}")
            return False

    async def create_relation_id_index(self) -> bool:
        query = """
        CREATE INDEX relation_id_index IF NOT EXISTS
        FOR ()-[r:RELATES]-()
        ON (r.id)
        """
        
        try:
            await self.client.execute_write(query)
            logger.info("Created relation_id_index")
            return True
        except Exception as e:
            logger.error(f"Failed to create relation_id_index: {e}")
            return False

    async def create_relation_type_index(self) -> bool:
        query = """
        CREATE INDEX relation_type_index IF NOT EXISTS
        FOR ()-[r:RELATES]-()
        ON (r.type)
        """
        
        try:
            await self.client.execute_write(query)
            logger.info("Created relation_type_index")
            return True
        except Exception as e:
            logger.error(f"Failed to create relation_type_index: {e}")
            return False

    async def ensure_indexes(self) -> Dict[str, bool]:
        results = {
            "entity_id_index": await self.create_entity_id_index(),
            "entity_name_index": await self.create_entity_name_index(),
            "entity_type_index": await self.create_entity_type_index(),
            "entity_fulltext": await self.create_fulltext_index(),
            "relation_id_index": await self.create_relation_id_index(),
            "relation_type_index": await self.create_relation_type_index()
        }
        
        success_count = sum(1 for v in results.values() if v)
        logger.info(f"Index creation completed: {success_count}/{len(results)} successful")
        
        return results

    async def list_indexes(self) -> List[Dict[str, Any]]:
        query = """
        SHOW INDEXES
        """
        
        try:
            result = await self.client.execute_read(query)
            return result
        except Exception as e:
            logger.error(f"Failed to list indexes: {e}")
            return []

    async def drop_index(self, index_name: str) -> bool:
        query = f"""
        DROP INDEX {index_name} IF EXISTS
        """
        
        try:
            await self.client.execute_write(query)
            logger.info(f"Dropped index: {index_name}")
            return True
        except Exception as e:
            logger.error(f"Failed to drop index {index_name}: {e}")
            return False


index_manager = IndexManager()
