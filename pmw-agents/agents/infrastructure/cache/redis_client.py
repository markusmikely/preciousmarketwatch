from __future__ import annotations
 
import logging
import os
 
log = logging.getLogger("pmw.infra.redis")

class RedisClient:
    def __init__(self):
        self._url = os.environ.get("REDIS_URL", "redis://localhost:6379")
        self._client = None

    # ── Lifecycle ──────────────────────────────────────────────────────────
 
    async def connect(self) -> None:
        """
        Open the Redis connection and verify it with PING.
        Safe to call multiple times — no-op if already connected.
        """
        if self._client is not None:
            return
        try:
            import redis.asyncio as aioredis
        except ImportError:
            raise ImportError(
                "redis[asyncio] is not installed. Run: pip install redis[asyncio]"
            )
        self._client = aioredis.from_url(
            self._url,
            decode_responses=True,
            socket_connect_timeout=5,
            socket_timeout=5,
            retry_on_timeout=True,
        )
        await self._client.ping()
        # Log URL with credentials stripped for safety
        safe_url = self._url.split("@")[-1] if "@" in self._url else self._url
        log.info("RedisClient connected", extra={"host": safe_url})
 
    async def close(self) -> None:
        """Close the Redis connection."""
        if self._client:
            await self._client.aclose()
            self._client = None
            log.info("RedisClient closed")
 
    def _get(self):
        """Return the client, raising clearly if connect() was never called."""
        if self._client is None:
            raise RuntimeError(
                "RedisClient.connect() has not been called. "
                "Ensure Infrastructure.connect() runs at worker startup."
            )
        return self._client

    # ── Pub/sub ────────────────────────────────────────────────────────────
 
    async def publish(self, channel: str, message: str) -> int:
        """
        Publish a message to a channel.
        Returns the number of subscribers that received it.
 
        Usage:
            await infra.redis.publish("pmw:events", json.dumps(event_payload))
        """
        return await self._get().publish(channel, message)
 
    # ── Key/value ──────────────────────────────────────────────────────────
 
    async def set(self, key: str, value: str, ex: int | None = None) -> None:
        """
        Set a string value. Optionally expire after `ex` seconds.
 
        Usage:
            await infra.redis.set("lock:topic:42", "1", ex=300)
        """
        await self._get().set(key, value, ex=ex)
 
    async def get(self, key: str) -> str | None:
        """
        Get a string value. Returns None if key does not exist.
        """
        return await self._get().get(key)
 
    async def delete(self, *keys: str) -> int:
        """Delete one or more keys. Returns count of deleted keys."""
        return await self._get().delete(*keys)
 
    async def exists(self, *keys: str) -> int:
        """Returns the number of keys that exist."""
        return await self._get().exists(*keys)
 
    # ── Streams (task queue) ───────────────────────────────────────────────
 
    async def xadd(
        self,
        stream: str,
        fields: dict[str, str],
        max_len: int = 10_000,
    ) -> str:
        """
        Append a message to a Redis Stream.
        Returns the auto-generated message ID.
 
        Usage:
            msg_id = await infra.redis.xadd(
                "pmw:tasks:research",
                {"run_id": "42", "topic_id": "7"},
            )
        """
        return await self._get().xadd(
            stream, fields, maxlen=max_len, approximate=True
        )
 
    async def xgroup_create(
        self,
        stream: str,
        group: str,
        mkstream: bool = True,
    ) -> None:
        """
        Create a consumer group for a stream.
        Silently ignores BUSYGROUP if the group already exists.
        """
        try:
            await self._get().xgroup_create(stream, group, id="0", mkstream=mkstream)
        except Exception as e:
            if "BUSYGROUP" not in str(e):
                raise
 
    async def xreadgroup(
        self,
        group: str,
        consumer: str,
        streams: dict[str, str],
        count: int = 1,
        block: int | None = None,
    ) -> list:
        """
        Read messages from a consumer group.
 
        Usage:
            messages = await infra.redis.xreadgroup(
                group="workers",
                consumer="worker-1",
                streams={"pmw:tasks:research": ">"},
                count=1,
                block=5000,   # ms to block waiting for messages
            )
        """
        return await self._get().xreadgroup(
            group, consumer, streams, count=count, block=block
        )
 
    async def xack(self, stream: str, group: str, *ids: str) -> int:
        """
        Acknowledge processed stream messages, removing them from the PEL.
 
        Usage:
            await infra.redis.xack("pmw:tasks:research", "workers", msg_id)
        """
        return await self._get().xack(stream, group, *ids)
 
    async def xpending(self, stream: str, group: str) -> dict:
        """Return summary of pending (unacknowledged) messages for a group."""
        return await self._get().xpending(stream, group)
 