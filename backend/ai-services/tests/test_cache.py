import pytest
from unittest.mock import MagicMock, patch, AsyncMock
import asyncio

from services.cache.memory_cache import MemoryCache
from services.cache.redis_cache import RedisCache


class TestMemoryCache:
    @pytest.fixture
    def cache(self):
        return MemoryCache(max_size=100, default_ttl=60)
    
    def test_set_and_get(self, cache):
        cache.set("test_key", "test_value")
        result = cache.get("test_key")
        
        assert result == "test_value"
    
    def test_get_nonexistent(self, cache):
        result = cache.get("nonexistent_key")
        
        assert result is None
    
    def test_delete(self, cache):
        cache.set("test_key", "test_value")
        deleted = cache.delete("test_key")
        
        assert deleted is True
        assert cache.get("test_key") is None
    
    def test_exists(self, cache):
        cache.set("test_key", "test_value")
        
        assert cache.exists("test_key") is True
        assert cache.exists("nonexistent") is False
    
    def test_clear(self, cache):
        cache.set("key1", "value1")
        cache.set("key2", "value2")
        cache.clear()
        
        assert cache.get("key1") is None
        assert cache.get("key2") is None
    
    def test_max_size_eviction(self):
        small_cache = MemoryCache(max_size=2, default_ttl=60)
        
        small_cache.set("key1", "value1")
        small_cache.set("key2", "value2")
        small_cache.set("key3", "value3")
        
        assert small_cache.get("key1") is None
        assert small_cache.get("key2") == "value2"
        assert small_cache.get("key3") == "value3"
    
    def test_get_stats(self, cache):
        cache.set("key1", "value1")
        cache.get("key1")
        cache.get("nonexistent")
        
        stats = cache.get_stats()
        
        assert stats["size"] == 1
        assert stats["hits"] == 1
        assert stats["misses"] == 1
    
    def test_embedding_cache(self, cache):
        text = "This is a test text"
        embedding = [0.1, 0.2, 0.3, 0.4, 0.5]
        
        cache.set_embedding(text, embedding)
        result = cache.get_embedding(text)
        
        assert result == embedding
    
    def test_search_result_cache(self, cache):
        query = "test query"
        result = {"doc1": 0.9, "doc2": 0.8}
        
        cache.set_search_result(query, result)
        cached = cache.get_search_result(query)
        
        assert cached == result


class TestRedisCache:
    @pytest.fixture
    def redis_cache(self):
        return RedisCache(host="localhost", port=6379)
    
    def test_make_key(self, redis_cache):
        key = redis_cache._make_key("test_key")
        
        assert key == "graphrag:test_key"
    
    def test_hash_text(self, redis_cache):
        hash1 = redis_cache._hash_text("test text")
        hash2 = redis_cache._hash_text("test text")
        hash3 = redis_cache._hash_text("different text")
        
        assert hash1 == hash2
        assert hash1 != hash3
    
    def test_is_connected_false_by_default(self, redis_cache):
        assert redis_cache.is_connected is False
    
    @pytest.mark.asyncio
    async def test_get_when_not_connected(self, redis_cache):
        result = await redis_cache.get("test_key")
        
        assert result is None
    
    @pytest.mark.asyncio
    async def test_set_when_not_connected(self, redis_cache):
        result = await redis_cache.set("test_key", "test_value")
        
        assert result is False
    
    @pytest.mark.asyncio
    async def test_get_embedding_when_not_connected(self, redis_cache):
        result = await redis_cache.get_embedding("test text")
        
        assert result is None
    
    @pytest.mark.asyncio
    async def test_get_stats_when_not_connected(self, redis_cache):
        stats = await redis_cache.get_stats()
        
        assert stats["connected"] is False


class TestCacheIntegration:
    def test_memory_cache_hit_rate(self):
        cache = MemoryCache(max_size=100)
        
        for i in range(10):
            cache.set(f"key_{i}", f"value_{i}")
        
        for i in range(10):
            cache.get(f"key_{i}")
        
        for i in range(5):
            cache.get(f"nonexistent_{i}")
        
        stats = cache.get_stats()
        
        assert stats["hits"] == 10
        assert stats["misses"] == 5
        expected_rate = 10 / 15
        assert abs(stats["hit_rate"] - expected_rate) < 0.01
    
    def test_memory_cache_ttl_expiration(self):
        import time
        cache = MemoryCache(max_size=100, default_ttl=1)
        
        cache.set("test_key", "test_value")
        
        result = cache.get("test_key")
        assert result == "test_value"
        
        time.sleep(1.1)
        
        result = cache.get("test_key")
        assert result is None
