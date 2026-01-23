"""Redis cache for user permissions."""

import hashlib
import json
import logging
from typing import Any

import redis.asyncio as redis

from .config import PluginSettings
from .exceptions import CacheError
from .models import UserPermissions

logger = logging.getLogger(__name__)


class PermissionCache:
    """Redis-based cache for user permissions."""

    CACHE_PREFIX = "tcloud:auth:permissions:"

    def __init__(self, settings: PluginSettings):
        """Initialize the permission cache.

        Args:
            settings: Plugin configuration settings.
        """
        self.settings = settings
        self._redis: redis.Redis | None = None

    async def initialize(self) -> None:
        """Initialize Redis connection."""
        try:
            self._redis = redis.from_url(
                self.settings.redis_url,
                encoding="utf-8",
                decode_responses=True,
            )
            # Test connection
            await self._redis.ping()
            logger.info("Redis cache initialized successfully")
        except redis.RedisError as e:
            logger.warning(f"Failed to connect to Redis: {e}. Cache disabled.")
            self._redis = None

    async def shutdown(self) -> None:
        """Close Redis connection."""
        if self._redis:
            await self._redis.close()
            self._redis = None

    @property
    def is_available(self) -> bool:
        """Check if cache is available."""
        return self._redis is not None

    async def get_permissions(self, email: str) -> UserPermissions | None:
        """Get cached permissions for a user.

        Args:
            email: User email address.

        Returns:
            Cached UserPermissions or None if not found/expired.
        """
        if not self._redis:
            return None

        cache_key = self._make_key(email)

        try:
            data = await self._redis.get(cache_key)
            if data:
                parsed = json.loads(data)
                logger.debug(f"Cache hit for {email}")
                return UserPermissions.from_cache_dict(parsed)
            logger.debug(f"Cache miss for {email}")
            return None
        except redis.RedisError as e:
            logger.warning(f"Redis get error: {e}")
            return None
        except (json.JSONDecodeError, ValueError) as e:
            logger.warning(f"Cache data parse error: {e}")
            return None

    async def set_permissions(
        self,
        email: str,
        permissions: UserPermissions,
        ttl: int | None = None,
    ) -> bool:
        """Cache user permissions.

        Args:
            email: User email address.
            permissions: UserPermissions to cache.
            ttl: Optional TTL override in seconds.

        Returns:
            True if cached successfully, False otherwise.
        """
        if not self._redis:
            return False

        cache_key = self._make_key(email)
        cache_ttl = ttl or self.settings.permission_cache_ttl

        try:
            data = json.dumps(permissions.to_cache_dict())
            await self._redis.set(cache_key, data, ex=cache_ttl)
            logger.debug(f"Cached permissions for {email} (TTL: {cache_ttl}s)")
            return True
        except redis.RedisError as e:
            logger.warning(f"Redis set error: {e}")
            return False

    async def invalidate(self, email: str) -> bool:
        """Invalidate cached permissions for a user.

        Args:
            email: User email address.

        Returns:
            True if invalidated, False otherwise.
        """
        if not self._redis:
            return False

        cache_key = self._make_key(email)

        try:
            result = await self._redis.delete(cache_key)
            logger.debug(f"Invalidated cache for {email}: {result}")
            return result > 0
        except redis.RedisError as e:
            logger.warning(f"Redis delete error: {e}")
            return False

    async def get_or_fetch(
        self,
        email: str,
        fetch_func,
        ttl: int | None = None,
    ) -> UserPermissions:
        """Get permissions from cache or fetch and cache.

        Args:
            email: User email address.
            fetch_func: Async function to fetch permissions if not cached.
            ttl: Optional TTL override in seconds.

        Returns:
            UserPermissions from cache or freshly fetched.
        """
        # Try cache first
        cached = await self.get_permissions(email)
        if cached:
            return cached

        # Fetch fresh data
        permissions = await fetch_func()

        # Cache the result (fire and forget)
        await self.set_permissions(email, permissions, ttl)

        return permissions

    def _make_key(self, email: str) -> str:
        """Generate cache key for email.

        Args:
            email: User email address.

        Returns:
            Cache key string.
        """
        # Use hash to handle special characters and keep keys short
        email_hash = hashlib.sha256(email.lower().encode()).hexdigest()[:16]
        return f"{self.CACHE_PREFIX}{email_hash}"


class TokenCache:
    """Redis-based cache for validated tokens."""

    CACHE_PREFIX = "tcloud:auth:token:"

    def __init__(self, settings: PluginSettings):
        """Initialize the token cache.

        Args:
            settings: Plugin configuration settings.
        """
        self.settings = settings
        self._redis: redis.Redis | None = None

    async def initialize(self, redis_client: redis.Redis | None = None) -> None:
        """Initialize Redis connection.

        Args:
            redis_client: Optional existing Redis client to reuse.
        """
        if redis_client:
            self._redis = redis_client
        else:
            try:
                self._redis = redis.from_url(
                    self.settings.redis_url,
                    encoding="utf-8",
                    decode_responses=True,
                )
                await self._redis.ping()
            except redis.RedisError as e:
                logger.warning(f"Failed to connect to Redis: {e}. Token cache disabled.")
                self._redis = None

    async def shutdown(self) -> None:
        """Close Redis connection."""
        if self._redis:
            await self._redis.close()
            self._redis = None

    async def is_token_valid(self, token_hash: str) -> bool | None:
        """Check if token was previously validated.

        Args:
            token_hash: Hash of the token.

        Returns:
            True if valid, False if invalid, None if not cached.
        """
        if not self._redis:
            return None

        cache_key = f"{self.CACHE_PREFIX}{token_hash}"

        try:
            result = await self._redis.get(cache_key)
            if result is None:
                return None
            return result == "1"
        except redis.RedisError:
            return None

    async def cache_token_result(
        self,
        token_hash: str,
        is_valid: bool,
        ttl: int = 60,
    ) -> None:
        """Cache token validation result.

        Args:
            token_hash: Hash of the token.
            is_valid: Whether the token is valid.
            ttl: Cache TTL in seconds.
        """
        if not self._redis:
            return

        cache_key = f"{self.CACHE_PREFIX}{token_hash}"

        try:
            await self._redis.set(cache_key, "1" if is_valid else "0", ex=ttl)
        except redis.RedisError:
            pass

    @staticmethod
    def hash_token(token: str) -> str:
        """Generate hash for token.

        Args:
            token: JWT token string.

        Returns:
            SHA256 hash of the token.
        """
        return hashlib.sha256(token.encode()).hexdigest()
