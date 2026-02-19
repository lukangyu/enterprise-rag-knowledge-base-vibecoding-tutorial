import redis.asyncio as redis
import json
import hashlib
import logging
from typing import Optional, Any, Dict, List
from datetime import timedelta

from config.settings import settings

logger = logging.getLogger(__name__)


class RedisCache:
    CACHE_TTL = {
        "embedding": 3600,
        "search_result": 300,
        "entity": 1800,
        "config": 600,
        "query_result": 180,
    }
    
    def __init__(
        self,
        host: str = "localhost",
        port: int = 6379,
        db: int = 0,
        password: Optional[str] = None,
        prefix: str = "graphrag:"
    ):
        self.host = host
        self.port = port
        self.db = db
        self.password = password
        self.prefix = prefix
        self._client: Optional[redis.Redis] = None
        self._connected = False
    
    async def connect(self):
        try:
            self._client = redis.Redis(
                host=self.host,
                port=self.port,
                db=self.db,
                password=self.password,
                decode_responses=True
            )
            await self._client.ping()
            self._connected = True
            logger.info(f"Redis connected: {self.host}:{self.port}")
        except Exception as e:
            logger.warning(f"Redis connection failed: {e}")
            self._connected = False
    
    async def disconnect(self):
        if self._client:
            await self._client.close()
            self._connected = False
    
    def _make_key(self, key: str) -> str:
        return f"{self.prefix}{key}"
    
    def _hash_text(self, text: str) -> str:
        return hashlib.md5(text.encode()).hexdigest()
    
    async def get(self, key: str) -> Optional[Any]:
        if not self._connected or not self._client:
            return None
        
        try:
            value = await self._client.get(self._make_key(key))
            if value:
                return json.loads(value)
            return None
        except Exception as e:
            logger.warning(f"Redis get failed: {e}")
            return None
    
    async def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None
    ) -> bool:
        if not self._connected or not self._client:
            return False
        
        try:
            serialized = json.dumps(value, ensure_ascii=False)
            full_key = self._make_key(key)
            
            if ttl:
                await self._client.setex(full_key, ttl, serialized)
            else:
                await self._client.set(full_key, serialized)
            
            return True
        except Exception as e:
            logger.warning(f"Redis set failed: {e}")
            return False
    
    async def delete(self, key: str) -> bool:
        if not self._connected or not self._client:
            return False
        
        try:
            await self._client.delete(self._make_key(key))
            return True
        except Exception as e:
            logger.warning(f"Redis delete failed: {e}")
            return False
    
    async def exists(self, key: str) -> bool:
        if not self._connected or not self._client:
            return False
        
        try:
            return await self._client.exists(self._make_key(key)) > 0
        except Exception as e:
            logger.warning(f"Redis exists failed: {e}")
            return False
    
    async def get_embedding(self, text: str) -> Optional[List[float]]:
        key = f"embedding:{self._hash_text(text)}"
        return await self.get(key)
    
    async def set_embedding(self, text: str, embedding: List[float]) -> bool:
        key = f"embedding:{self._hash_text(text)}"
        return await self.set(key, embedding, self.CACHE_TTL["embedding"])
    
    async def get_search_result(self, query: str, filters: Dict = None) -> Optional[Dict]:
        filter_str = json.dumps(filters or {}, sort_keys=True)
        key = f"search:{self._hash_text(query + filter_str)}"
        return await self.get(key)
    
    async def set_search_result(self, query: str, result: Dict, filters: Dict = None) -> bool:
        filter_str = json.dumps(filters or {}, sort_keys=True)
        key = f"search:{self._hash_text(query + filter_str)}"
        return await self.set(key, result, self.CACHE_TTL["search_result"])
    
    async def get_entity(self, entity_id: str) -> Optional[Dict]:
        key = f"entity:{entity_id}"
        return await self.get(key)
    
    async def set_entity(self, entity_id: str, entity: Dict) -> bool:
        key = f"entity:{entity_id}"
        return await self.set(key, entity, self.CACHE_TTL["entity"])
    
    async def invalidate_pattern(self, pattern: str) -> int:
        if not self._connected or not self._client:
            return 0
        
        try:
            keys = []
            async for key in self._client.scan_iter(match=self._make_key(pattern)):
                keys.append(key)
            
            if keys:
                return await self._client.delete(*keys)
            return 0
        except Exception as e:
            logger.warning(f"Redis invalidate_pattern failed: {e}")
            return 0
    
    async def get_stats(self) -> Dict[str, Any]:
        if not self._connected or not self._client:
            return {"connected": False}
        
        try:
            info = await self._client.info()
            return {
                "connected": True,
                "used_memory": info.get("used_memory_human", "unknown"),
                "connected_clients": info.get("connected_clients", 0),
                "total_commands_processed": info.get("total_commands_processed", 0),
                "keyspace_hits": info.get("keyspace_hits", 0),
                "keyspace_misses": info.get("keyspace_misses", 0),
            }
        except Exception as e:
            return {"connected": False, "error": str(e)}
    
    @property
    def is_connected(self) -> bool:
        return self._connected


redis_cache = RedisCache(
    host=getattr(settings, 'REDIS_HOST', 'localhost'),
    port=getattr(settings, 'REDIS_PORT', 6379),
)
