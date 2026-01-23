"""Pytest fixtures for TCloud Cognito Auth Plugin tests."""

import json
import os
from datetime import datetime, timedelta, timezone
from typing import Any, Generator
from unittest.mock import AsyncMock, MagicMock

import pytest
from jose import jwt

# Set test environment variables before importing config
os.environ.setdefault("COGNITO_USER_POOL_ID", "us-east-2_TestPool123")
os.environ.setdefault("COGNITO_REGION", "us-east-2")
os.environ.setdefault("COGNITO_APP_CLIENT_ID", "test-client-id-123")
os.environ.setdefault("TCLOUD_API_URL", "https://api.tcloud.test")
os.environ.setdefault("TCLOUD_API_KEY", "test-api-key")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")


@pytest.fixture
def test_settings():
    """Create test settings."""
    from tcloud_cognito_auth.config import PluginSettings

    return PluginSettings(
        cognito_user_pool_id="us-east-2_TestPool123",
        cognito_region="us-east-2",
        cognito_app_client_id="test-client-id-123",
        tcloud_api_url="https://api.tcloud.test",
        tcloud_api_key="test-api-key",
        redis_url="redis://localhost:6379/0",
        permission_cache_ttl=300,
    )


@pytest.fixture
def sample_jwks() -> dict[str, Any]:
    """Sample JWKS for testing."""
    return {
        "keys": [
            {
                "kty": "RSA",
                "kid": "test-key-id-1",
                "use": "sig",
                "alg": "RS256",
                "n": "0vx7agoebGcQSuuPiLJXZptN9nndrQmbXEps2aiAFbWhM78LhWx4cbbfAAtVT86zwu1RK7aPFFxuhDR1L6tSoc_BJECPebWKRXjBZCiFV4n3oknjhMstn64tZ_2W-5JsGY4Hc5n9yBXArwl93lqt7_RN5w6Cf0h4QyQ5v-65YGjQR0_FDW2QvzqY368QQMicAtaSqzs8KJZgnYb9c7d0zgdAZHzu6qMQvRL5hajrn1n91CbOpbISD08qNLyrdkt-bFTWhAI4vMQFh6WeZu0fM4lFd2NcRwr3XPksINHaQ-G_xBniIqbw0Ls1jF44-csFCur-kEgU8awapJzKnqDKgw",
                "e": "AQAB",
            }
        ]
    }


@pytest.fixture
def sample_access_token_claims() -> dict[str, Any]:
    """Sample access token claims."""
    now = datetime.now(timezone.utc)
    return {
        "sub": "12345678-1234-1234-1234-123456789012",
        "iss": "https://cognito-idp.us-east-2.amazonaws.com/us-east-2_TestPool123",
        "token_use": "access",
        "client_id": "test-client-id-123",
        "username": "google_user@example.com",
        "exp": int((now + timedelta(hours=1)).timestamp()),
        "iat": int(now.timestamp()),
        "scope": "openid email profile",
    }


@pytest.fixture
def sample_id_token_claims() -> dict[str, Any]:
    """Sample ID token claims."""
    now = datetime.now(timezone.utc)
    return {
        "sub": "12345678-1234-1234-1234-123456789012",
        "iss": "https://cognito-idp.us-east-2.amazonaws.com/us-east-2_TestPool123",
        "token_use": "id",
        "aud": "test-client-id-123",
        "email": "user@example.com",
        "name": "Test User",
        "exp": int((now + timedelta(hours=1)).timestamp()),
        "iat": int(now.timestamp()),
    }


@pytest.fixture
def expired_token_claims(sample_access_token_claims) -> dict[str, Any]:
    """Expired token claims."""
    now = datetime.now(timezone.utc)
    claims = sample_access_token_claims.copy()
    claims["exp"] = int((now - timedelta(hours=1)).timestamp())
    return claims


@pytest.fixture
def sample_user_permissions() -> dict[str, Any]:
    """Sample user permissions from TCloud API."""
    return {
        "email": "user@example.com",
        "customers": ["cloud-001", "cloud-002", "cloud-003"],
        "roles": ["viewer", "operator"],
        "permissions": ["read:metrics", "read:logs", "write:alerts"],
    }


@pytest.fixture
def mock_http_client():
    """Create a mock HTTP client."""
    client = AsyncMock()
    return client


@pytest.fixture
def mock_redis_client():
    """Create a mock Redis client."""
    client = AsyncMock()
    client.get = AsyncMock(return_value=None)
    client.set = AsyncMock(return_value=True)
    client.delete = AsyncMock(return_value=1)
    return client
