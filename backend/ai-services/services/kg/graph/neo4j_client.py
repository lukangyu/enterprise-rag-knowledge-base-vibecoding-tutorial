import logging
from typing import Optional, List, Dict, Any
from neo4j import AsyncGraphDatabase, AsyncDriver, AsyncSession
from neo4j.exceptions import ServiceUnavailable

from config.kg_settings import kg_settings

logger = logging.getLogger(__name__)


class Neo4jClient:
    _instance: Optional["Neo4jClient"] = None

    def __new__(cls) -> "Neo4jClient":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._driver: Optional[AsyncDriver] = None
        return cls._instance

    async def connect(self) -> bool:
        try:
            self._driver = AsyncGraphDatabase.driver(
                kg_settings.NEO4J_URI,
                auth=(kg_settings.NEO4J_USERNAME, kg_settings.NEO4J_PASSWORD),
                max_connection_pool_size=kg_settings.NEO4J_MAX_CONNECTION_POOL_SIZE,
                connection_timeout=kg_settings.NEO4J_CONNECTION_TIMEOUT,
                max_transaction_retry_time=kg_settings.NEO4J_MAX_TRANSACTION_RETRY_TIME
            )
            await self._driver.verify_connectivity()
            logger.info(f"Connected to Neo4j at {kg_settings.NEO4J_URI}")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to Neo4j: {e}")
            return False

    async def close(self) -> None:
        if self._driver:
            await self._driver.close()
            self._driver = None
            logger.info("Disconnected from Neo4j")

    def get_session(self) -> AsyncSession:
        if self._driver is None:
            raise RuntimeError("Neo4j driver not initialized. Call connect() first.")
        return self._driver.session(database=kg_settings.NEO4J_DATABASE)

    async def health_check(self) -> bool:
        try:
            if self._driver is None:
                return False
            await self._driver.verify_connectivity()
            return True
        except ServiceUnavailable:
            return False
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return False

    async def execute_query(
        self,
        query: str,
        parameters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        parameters = parameters or {}
        async with self.get_session() as session:
            result = await session.run(query, parameters)
            records = await result.data()
            return records

    async def execute_write(
        self,
        query: str,
        parameters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        parameters = parameters or {}
        async with self.get_session() as session:
            result = await session.execute_write(
                lambda tx: tx.run(query, parameters).data()
            )
            return result

    async def execute_read(
        self,
        query: str,
        parameters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        parameters = parameters or {}
        async with self.get_session() as session:
            result = await session.execute_read(
                lambda tx: tx.run(query, parameters).data()
            )
            return result

    @property
    def driver(self) -> AsyncDriver:
        if self._driver is None:
            raise RuntimeError("Neo4j driver not initialized. Call connect() first.")
        return self._driver


neo4j_client = Neo4jClient()
