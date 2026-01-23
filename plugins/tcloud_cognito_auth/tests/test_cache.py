"""Tests for Redis cache."""

import json
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from tcloud_cognito_auth.cache import PermissionCache, TokenCache
from tcloud_cognito_auth.models import UserPermissions


@pytest.fixture
def permission_cache(test_settings):
    """Create a permission cache instance."""
    return PermissionCache(test_settings)


@pytest.fixture
def token_cache(test_settings):
    """Create a token cache instance."""
    return TokenCache(test_settings)


@pytest.fixture
def sample_permissions():
    """Create sample permissions."""
    return UserPermissions(
        email="user@example.com",
        customers=["cloud-001", "cloud-002"],
        roles=["viewer"],
        permissions=["read:metrics"],
        fetched_at=datetime(2024, 1, 15, 12, 0, 0),
    )


class TestPermissionCache:
    """Tests for PermissionCache."""

    @pytest.mark.asyncio
    async def test_is_available_false_when_no_redis(self, permission_cache):
        """Test is_available returns False without Redis."""
        assert permission_cache.is_available is False

    @pytest.mark.asyncio
    async def test_is_available_true_with_redis(self, permission_cache):
        """Test is_available returns True with Redis."""
        permission_cache._redis = AsyncMock()
        assert permission_cache.is_available is True

    @pytest.mark.asyncio
    async def test_get_permissions_returns_none_without_redis(self, permission_cache):
        """Test get returns None when Redis is unavailable."""
        result = await permission_cache.get_permissions("user@example.com")
        assert result is None

    @pytest.mark.asyncio
    async def test_get_permissions_cache_miss(self, permission_cache):
        """Test get returns None on cache miss."""
        mock_redis = AsyncMock()
        mock_redis.get = AsyncMock(return_value=None)
        permission_cache._redis = mock_redis

        result = await permission_cache.get_permissions("user@example.com")
        assert result is None

    @pytest.mark.asyncio
    async def test_get_permissions_cache_hit(
        self, permission_cache, sample_permissions
    ):
        """Test get returns cached permissions."""
        mock_redis = AsyncMock()
        mock_redis.get = AsyncMock(
            return_value=json.dumps(sample_permissions.to_cache_dict())
        )
        permission_cache._redis = mock_redis

        result = await permission_cache.get_permissions("user@example.com")

        assert result is not None
        assert result.email == "user@example.com"
        assert "cloud-001" in result.customers

    @pytest.mark.asyncio
    async def test_set_permissions_success(
        self, permission_cache, sample_permissions
    ):
        """Test setting permissions in cache."""
        mock_redis = AsyncMock()
        mock_redis.set = AsyncMock(return_value=True)
        permission_cache._redis = mock_redis

        result = await permission_cache.set_permissions(
            "user@example.com", sample_permissions
        )

        assert result is True
        mock_redis.set.assert_called_once()

    @pytest.mark.asyncio
    async def test_set_permissions_with_custom_ttl(
        self, permission_cache, sample_permissions
    ):
        """Test setting permissions with custom TTL."""
        mock_redis = AsyncMock()
        mock_redis.set = AsyncMock(return_value=True)
        permission_cache._redis = mock_redis

        await permission_cache.set_permissions(
            "user@example.com", sample_permissions, ttl=600
        )

        call_args = mock_redis.set.call_args
        assert call_args[1]["ex"] == 600

    @pytest.mark.asyncio
    async def test_invalidate_success(self, permission_cache):
        """Test invalidating cached permissions."""
        mock_redis = AsyncMock()
        mock_redis.delete = AsyncMock(return_value=1)
        permission_cache._redis = mock_redis

        result = await permission_cache.invalidate("user@example.com")

        assert result is True

    @pytest.mark.asyncio
    async def test_invalidate_not_found(self, permission_cache):
        """Test invalidating non-existent cache entry."""
        mock_redis = AsyncMock()
        mock_redis.delete = AsyncMock(return_value=0)
        permission_cache._redis = mock_redis

        result = await permission_cache.invalidate("user@example.com")

        assert result is False

    @pytest.mark.asyncio
    async def test_get_or_fetch_from_cache(
        self, permission_cache, sample_permissions
    ):
        """Test get_or_fetch returns cached value."""
        mock_redis = AsyncMock()
        mock_redis.get = AsyncMock(
            return_value=json.dumps(sample_permissions.to_cache_dict())
        )
        permission_cache._redis = mock_redis

        fetch_func = AsyncMock()

        result = await permission_cache.get_or_fetch(
            "user@example.com", fetch_func
        )

        assert result.email == "user@example.com"
        fetch_func.assert_not_called()

    @pytest.mark.asyncio
    async def test_get_or_fetch_fetches_on_miss(
        self, permission_cache, sample_permissions
    ):
        """Test get_or_fetch fetches and caches on miss."""
        mock_redis = AsyncMock()
        mock_redis.get = AsyncMock(return_value=None)
        mock_redis.set = AsyncMock(return_value=True)
        permission_cache._redis = mock_redis

        fetch_func = AsyncMock(return_value=sample_permissions)

        result = await permission_cache.get_or_fetch(
            "user@example.com", fetch_func
        )

        assert result.email == "user@example.com"
        fetch_func.assert_called_once()
        mock_redis.set.assert_called_once()

    def test_make_key_consistent(self, permission_cache):
        """Test key generation is consistent."""
        key1 = permission_cache._make_key("user@example.com")
        key2 = permission_cache._make_key("user@example.com")
        key3 = permission_cache._make_key("USER@EXAMPLE.COM")

        assert key1 == key2
        assert key1 == key3  # Case insensitive

    def test_make_key_different_emails(self, permission_cache):
        """Test different emails produce different keys."""
        key1 = permission_cache._make_key("user1@example.com")
        key2 = permission_cache._make_key("user2@example.com")

        assert key1 != key2


class TestTokenCache:
    """Tests for TokenCache."""

    def test_hash_token(self):
        """Test token hashing."""
        hash1 = TokenCache.hash_token("token123")
        hash2 = TokenCache.hash_token("token123")
        hash3 = TokenCache.hash_token("token456")

        assert hash1 == hash2
        assert hash1 != hash3
        assert len(hash1) == 64  # SHA256 hex length

    @pytest.mark.asyncio
    async def test_is_token_valid_not_cached(self, token_cache):
        """Test checking uncached token."""
        mock_redis = AsyncMock()
        mock_redis.get = AsyncMock(return_value=None)
        token_cache._redis = mock_redis

        result = await token_cache.is_token_valid("somehash")
        assert result is None

    @pytest.mark.asyncio
    async def test_is_token_valid_cached_valid(self, token_cache):
        """Test checking cached valid token."""
        mock_redis = AsyncMock()
        mock_redis.get = AsyncMock(return_value="1")
        token_cache._redis = mock_redis

        result = await token_cache.is_token_valid("somehash")
        assert result is True

    @pytest.mark.asyncio
    async def test_is_token_valid_cached_invalid(self, token_cache):
        """Test checking cached invalid token."""
        mock_redis = AsyncMock()
        mock_redis.get = AsyncMock(return_value="0")
        token_cache._redis = mock_redis

        result = await token_cache.is_token_valid("somehash")
        assert result is False

    @pytest.mark.asyncio
    async def test_cache_token_result(self, token_cache):
        """Test caching token validation result."""
        mock_redis = AsyncMock()
        mock_redis.set = AsyncMock(return_value=True)
        token_cache._redis = mock_redis

        await token_cache.cache_token_result("somehash", True, ttl=120)

        mock_redis.set.assert_called_once()
        call_args = mock_redis.set.call_args
        assert call_args[0][1] == "1"
        assert call_args[1]["ex"] == 120
