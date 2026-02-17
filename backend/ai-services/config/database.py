from pymilvus import connections, utility
from .settings import settings
import logging

logger = logging.getLogger(__name__)


class MilvusConnection:
    _instance = None

    def __new__(cls) -> "MilvusConnection":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def connect(self) -> bool:
        try:
            connections.connect(
                alias="default",
                host=settings.MILVUS_HOST,
                port=settings.MILVUS_PORT
            )
            logger.info(f"Connected to Milvus at {settings.MILVUS_HOST}:{settings.MILVUS_PORT}")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to Milvus: {e}")
            return False

    def disconnect(self) -> None:
        try:
            connections.disconnect("default")
            logger.info("Disconnected from Milvus")
        except Exception as e:
            logger.error(f"Failed to disconnect from Milvus: {e}")

    def is_connected(self) -> bool:
        try:
            return connections.has_connection("default")
        except Exception:
            return False


milvus_connection = MilvusConnection()
