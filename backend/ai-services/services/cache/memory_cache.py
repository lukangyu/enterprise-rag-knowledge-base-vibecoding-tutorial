import time
import json
import hashlib
import logging
from typing import Optional, Any, Dict, List
from collections import OrderedDict
from threading import Lock

logger = logging.getLogger(__name__)


class MemoryCache:
    def __init__(self, max_size: int = 1000, default_ttl: int = 300):
        self.max_size = max_size
        self.default_ttl = default_ttl
        self._cache: OrderedDict = OrderedDict()
        self._lock = Lock()
        self._hits = 0
        self._misses = 0
    
    def _hash_key(self, key: str) -> str:
        return hashlib.md5(key.encode()).hexdigest()
    
    def _is_expired(self, item: Dict) -> bool:
        return time.time() > item.get("expires_at", 0)
    
    def get(self, key: str) -> Optional[Any]:
        with self._lock:
            hashed_key = self._hash_key(key)
            
            if hashed_key not in self._cache:
                self._misses += 1
                return None
            
            item = self._cache[hashed_key]
            
            if self._is_expired(item):
                del self._cache[hashed_key]
                self._misses += 1
                return None
            
            self._cache.move_to_end(hashed_key)
            self._hits += 1
            return item.get("value")
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        with self._lock:
            hashed_key = self._hash_key(key)
            
            if len(self._cache) >= self.max_size:
                self._cache.popitem(last=False)
            
            self._cache[hashed_key] = {
                "value": value,
                "expires_at": time.time() + (ttl or self.default_ttl)
            }
            
            return True
    
    def delete(self, key: str) -> bool:
        with self._lock:
            hashed_key = self._hash_key(key)
            if hashed_key in self._cache:
                del self._cache[hashed_key]
                return True
            return False
    
    def exists(self, key: str) -> bool:
        with self._lock:
            hashed_key = self._hash_key(key)
            if hashed_key not in self._cache:
                return False
            
            item = self._cache[hashed_key]
            if self._is_expired(item):
                del self._cache[hashed_key]
                return False
            
            return True
    
    def clear(self):
        with self._lock:
            self._cache.clear()
            self._hits = 0
            self._misses = 0
    
    def get_stats(self) -> Dict[str, Any]:
        with self._lock:
            total_requests = self._hits + self._misses
            hit_rate = self._hits / total_requests if total_requests > 0 else 0
            
            return {
                "size": len(self._cache),
                "max_size": self.max_size,
                "hits": self._hits,
                "misses": self._misses,
                "hit_rate": round(hit_rate, 4),
                "total_requests": total_requests
            }
    
    def cleanup_expired(self) -> int:
        with self._lock:
            expired_keys = [
                k for k, v in self._cache.items()
                if self._is_expired(v)
            ]
            
            for key in expired_keys:
                del self._cache[key]
            
            return len(expired_keys)
    
    def get_embedding(self, text: str) -> Optional[List[float]]:
        key = f"embedding:{self._hash_key(text)}"
        return self.get(key)
    
    def set_embedding(self, text: str, embedding: List[float], ttl: int = 3600) -> bool:
        key = f"embedding:{self._hash_key(text)}"
        return self.set(key, embedding, ttl)
    
    def get_search_result(self, query: str, filters: Dict = None) -> Optional[Dict]:
        filter_str = json.dumps(filters or {}, sort_keys=True)
        key = f"search:{self._hash_key(query + filter_str)}"
        return self.get(key)
    
    def set_search_result(self, query: str, result: Dict, filters: Dict = None, ttl: int = 300) -> bool:
        filter_str = json.dumps(filters or {}, sort_keys=True)
        key = f"search:{self._hash_key(query + filter_str)}"
        return self.set(key, result, ttl)


memory_cache = MemoryCache()
