"""Tests for Cognito JWT validation."""

import time
from unittest.mock import AsyncMock, patch

import httpx
import pytest

from tcloud_cognito_auth.cognito import CognitoJWTValidator
from tcloud_cognito_auth.exceptions import (
    InvalidAudienceError,
    JWKSFetchError,
    KeyNotFoundError,
    TokenExpiredError,
    TokenValidationError,
)


@pytest.fixture
def validator(test_settings):
    """Create a validator instance."""
    return CognitoJWTValidator(test_settings)


class TestCognitoJWTValidator:
    """Tests for CognitoJWTValidator."""

    @pytest.mark.asyncio
    async def test_initialize_and_shutdown(self, validator):
        """Test validator initialization and shutdown."""
        with patch.object(validator, "_refresh_jwks", new_callable=AsyncMock):
            await validator.initialize()
            assert validator._http_client is not None

            await validator.shutdown()
            assert validator._http_client is None

    @pytest.mark.asyncio
    async def test_get_jwks_uses_cache(self, validator, sample_jwks):
        """Test that JWKS is cached."""
        validator._jwks_cache = sample_jwks
        validator._jwks_cache_time = time.time()

        jwks = await validator._get_jwks()
        assert jwks == sample_jwks

    @pytest.mark.asyncio
    async def test_get_jwks_refreshes_when_expired(self, validator, sample_jwks):
        """Test that JWKS is refreshed when cache expires."""
        validator._jwks_cache = sample_jwks
        validator._jwks_cache_time = time.time() - 7200  # 2 hours ago

        with patch.object(validator, "_refresh_jwks", new_callable=AsyncMock) as mock:
            await validator._get_jwks()
            mock.assert_called_once()

    @pytest.mark.asyncio
    async def test_refresh_jwks_success(self, validator, sample_jwks):
        """Test successful JWKS refresh."""
        mock_response = AsyncMock()
        mock_response.json.return_value = sample_jwks
        mock_response.raise_for_status = AsyncMock()

        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_response)
        validator._http_client = mock_client

        await validator._refresh_jwks()

        assert validator._jwks_cache == sample_jwks
        assert validator._jwks_cache_time > 0

    @pytest.mark.asyncio
    async def test_refresh_jwks_failure_without_cache(self, validator):
        """Test JWKS refresh failure without cached data."""
        mock_client = AsyncMock()
        mock_client.get = AsyncMock(side_effect=httpx.HTTPError("Connection failed"))
        validator._http_client = mock_client
        validator._jwks_cache = None

        with pytest.raises(JWKSFetchError):
            await validator._refresh_jwks()

    @pytest.mark.asyncio
    async def test_refresh_jwks_failure_with_cache_fallback(
        self, validator, sample_jwks
    ):
        """Test JWKS refresh failure falls back to cache."""
        mock_client = AsyncMock()
        mock_client.get = AsyncMock(side_effect=httpx.HTTPError("Connection failed"))
        validator._http_client = mock_client
        validator._jwks_cache = sample_jwks

        # Should not raise, just use cached value
        await validator._refresh_jwks()
        assert validator._jwks_cache == sample_jwks

    @pytest.mark.asyncio
    async def test_get_signing_key_found(self, validator, sample_jwks):
        """Test getting signing key by kid."""
        validator._jwks_cache = sample_jwks
        validator._jwks_cache_time = time.time()

        key = await validator._get_signing_key("test-key-id-1")
        assert key["kid"] == "test-key-id-1"

    @pytest.mark.asyncio
    async def test_get_signing_key_not_found(self, validator, sample_jwks):
        """Test key not found error."""
        validator._jwks_cache = sample_jwks
        validator._jwks_cache_time = time.time()

        with patch.object(validator, "_refresh_jwks", new_callable=AsyncMock):
            with pytest.raises(KeyNotFoundError):
                await validator._get_signing_key("non-existent-key")

    def test_extract_token_from_header_valid(self, validator):
        """Test extracting token from valid header."""
        token = validator.extract_token_from_header("Bearer abc123")
        assert token == "abc123"

    def test_extract_token_from_header_invalid(self, validator):
        """Test extracting token from invalid headers."""
        assert validator.extract_token_from_header(None) is None
        assert validator.extract_token_from_header("") is None
        assert validator.extract_token_from_header("Basic abc123") is None
        assert validator.extract_token_from_header("Bearer") is None
        assert validator.extract_token_from_header("abc123") is None


class TestTokenValidation:
    """Tests for token validation logic."""

    @pytest.mark.asyncio
    async def test_validate_token_missing_kid(self, validator):
        """Test validation fails for token without kid."""
        # Create a token without kid in header
        with patch("jose.jwt.get_unverified_header", return_value={}):
            with pytest.raises(TokenValidationError, match="missing 'kid'"):
                await validator.validate_token("invalid.token.here")

    @pytest.mark.asyncio
    async def test_validate_token_invalid_client_id(
        self, validator, sample_jwks, sample_access_token_claims
    ):
        """Test validation fails for invalid client_id."""
        # This would require a properly signed token which is complex to mock
        # In real tests, we'd use a test RSA key pair
        pass  # Placeholder for integration test

    @pytest.mark.asyncio
    async def test_validate_token_expired(self, validator):
        """Test validation fails for expired token."""
        # Placeholder - requires properly signed expired token
        pass
