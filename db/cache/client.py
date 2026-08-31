from typing import Optional

import redis

REDIS_HOST = "127.0.0.1"
REDIS_PORT = 6379

client = redis.Redis(
    host=REDIS_HOST,
    port=REDIS_PORT,
    decode_responses=True,
    socket_connect_timeout=3,
)

DEFAULT_TTL_SECONDS = 3600  # 1h


def cache_set(key: str, value: str, ttl: Optional[int] = DEFAULT_TTL_SECONDS) -> None:
    """Store a string value in Redis under *key*.

    Args:
        key: Redis key.
        value: String payload.
        ttl: Expiration in seconds. Pass ``None`` for a persistent key
            (useful for pipeline metadata that must survive between stages).
    """
    client.set(key, value, ex=ttl)


def cache_get(key: str) -> Optional[str]:
    """Retrieve a string value from Redis, or ``None`` if the key doesn't exist."""
    return client.get(key)


def cache_delete(*keys: str) -> int:
    """Delete one or more Redis keys. Returns the number of keys removed."""
    if not keys:
        return 0
    return int(client.delete(*keys))