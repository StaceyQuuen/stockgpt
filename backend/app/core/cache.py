import json
import logging

log = logging.getLogger(__name__)


class Cache:
    """容错缓存：Redis 不可用时自动降级为内存缓存，不阻塞调用方"""

    _redis_client = None
    _redis_checked = False
    _memory_cache = {}

    def __init__(self):
        if not Cache._redis_checked:
            self._init_redis()

    def _init_redis(self):
        try:
            import redis
            client = redis.Redis(
                host="localhost",
                port=6379,
                decode_responses=True,
                socket_connect_timeout=0.5,
                socket_timeout=0.5,
            )
            client.ping()
            Cache._redis_client = client
        except Exception as e:
            log.warning(f"Redis unavailable, falling back to memory cache: {e}")
            Cache._redis_client = None
        finally:
            Cache._redis_checked = True

    def set(self, key, value, ttl=300):
        if Cache._redis_client is None:
            Cache._memory_cache[key] = (value, ttl)
            return
        try:
            Cache._redis_client.set(key, json.dumps(value), ex=ttl)
        except Exception as e:
            log.warning(f"Redis set failed, using memory cache: {e}")
            Cache._memory_cache[key] = (value, ttl)

    def get(self, key):
        if Cache._redis_client is None:
            entry = Cache._memory_cache.get(key)
            return entry[0] if entry else None
        try:
            data = Cache._redis_client.get(key)
            return json.loads(data) if data else None
        except Exception as e:
            log.warning(f"Redis get failed, using memory cache: {e}")
            entry = Cache._memory_cache.get(key)
            return entry[0] if entry else None
