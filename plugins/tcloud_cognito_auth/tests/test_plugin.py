"""Tests for the main plugin."""

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from tcloud_cognito_auth.exceptions import TokenExpiredError, TokenValidationError
from tcloud_cognito_auth.models import AuthenticatedUser, CognitoClaims, UserPermissions
from tcloud_cognito_auth.tcloud_cognito_auth import TCloudCognitoAuthPlugin


@pytest.fixture
def plugin(test_settings):
    """Create a plugin instance with test settings."""
    plugin = TCloudCognitoAuthPlugin()
    plugin._settings = test_settings
    return plugin


@pytest.fixture
def mock_cognito_validator():
    """Create a mock Cognito validator."""
    return AsyncMock()


@pytest.fixture
def mock_tcloud_client():
    """Create a mock TCloud client."""
    return AsyncMock()


@pytest.fixture
def mock_permission_cache():
    """Create a mock permission cache."""
    cache = AsyncMock()
    cache.get_or_fetch = AsyncMock()
    return cache


@pytest.fixture
def sample_claims():
    """Create sample Cognito claims."""
    return CognitoClaims(
        sub="12345678-1234-1234-1234-123456789012",
        iss="https://cognito-idp.sa-east-1.amazonaws.com/sa-east-1_TestPool123",
        token_use="access",
        client_id="test-client-id-123",
        username="google_user@example.com",
        exp=9999999999,
        iat=1000000000,
        name="Test User",
    )


@pytest.fixture
def sample_user_permissions():
    """Create sample user permissions."""
    return UserPermissions(
        email="user@example.com",
        customers=["cloud-001", "cloud-002"],
        roles=["viewer"],
        permissions=["read:metrics"],
    )


class TestTCloudCognitoAuthPlugin:
    """Tests for TCloudCognitoAuthPlugin."""

    @pytest.mark.asyncio
    async def test_initialize_and_shutdown(self, plugin):
        """Test plugin initialization and shutdown."""
        with patch.object(plugin, "_cognito_validator") as mock_validator, \
             patch.object(plugin, "_tcloud_client") as mock_client, \
             patch.object(plugin, "_permission_cache") as mock_cache:

            mock_validator = AsyncMock()
            mock_client = AsyncMock()
            mock_cache = AsyncMock()

            plugin._cognito_validator = mock_validator
            plugin._tcloud_client = mock_client
            plugin._permission_cache = mock_cache
            plugin._initialized = True

            await plugin.shutdown()

            assert plugin._initialized is False

    @pytest.mark.asyncio
    async def test_http_auth_resolve_user_no_token(self, plugin):
        """Test auth with no bearer token."""
        plugin._initialized = True

        result = await plugin.http_auth_resolve_user({
            "credentials": {}
        })

        assert result["continue_processing"] is True
        assert "modified_payload" not in result

    @pytest.mark.asyncio
    async def test_http_auth_resolve_user_non_bearer(self, plugin):
        """Test auth with non-bearer scheme."""
        plugin._initialized = True

        result = await plugin.http_auth_resolve_user({
            "credentials": {
                "credentials": "sometoken",
                "scheme": "basic"
            }
        })

        assert result["continue_processing"] is True

    @pytest.mark.asyncio
    async def test_http_auth_resolve_user_success(
        self, plugin, sample_claims, sample_user_permissions
    ):
        """Test successful authentication."""
        plugin._initialized = True

        # Mock dependencies
        mock_validator = AsyncMock()
        mock_validator.validate_token = AsyncMock(return_value=sample_claims)
        plugin._cognito_validator = mock_validator

        mock_cache = AsyncMock()
        mock_cache.get_or_fetch = AsyncMock(return_value=sample_user_permissions)
        plugin._permission_cache = mock_cache

        result = await plugin.http_auth_resolve_user({
            "credentials": {
                "credentials": "valid.jwt.token",
                "scheme": "bearer"
            }
        })

        assert result["continue_processing"] is True
        assert "modified_payload" in result
        assert result["modified_payload"]["email"] == "user@example.com"
        assert "metadata" in result
        assert result["metadata"]["auth_method"] == "cognito"

    @pytest.mark.asyncio
    async def test_http_auth_resolve_user_expired_token(self, plugin):
        """Test authentication with expired token."""
        plugin._initialized = True

        mock_validator = AsyncMock()
        mock_validator.validate_token = AsyncMock(
            side_effect=TokenExpiredError("Token expired")
        )
        plugin._cognito_validator = mock_validator

        result = await plugin.http_auth_resolve_user({
            "credentials": {
                "credentials": "expired.jwt.token",
                "scheme": "bearer"
            }
        })

        assert result["continue_processing"] is False
        assert "error" in result
        assert result["error"]["code"] == "TOKEN_EXPIRED"

    @pytest.mark.asyncio
    async def test_http_auth_resolve_user_invalid_token(self, plugin):
        """Test authentication with invalid token."""
        plugin._initialized = True

        mock_validator = AsyncMock()
        mock_validator.validate_token = AsyncMock(
            side_effect=TokenValidationError("Invalid token", "INVALID_TOKEN")
        )
        plugin._cognito_validator = mock_validator

        result = await plugin.http_auth_resolve_user({
            "credentials": {
                "credentials": "invalid.jwt.token",
                "scheme": "bearer"
            }
        })

        assert result["continue_processing"] is False
        assert "error" in result


class TestAgentPreInvoke:
    """Tests for agent_pre_invoke hook."""

    @pytest.mark.asyncio
    async def test_agent_pre_invoke_no_user(self, plugin):
        """Test pre_invoke with no authenticated user."""
        plugin._initialized = True

        result = await plugin.agent_pre_invoke(
            {"headers": {}},
            context={}
        )

        assert result["continue_processing"] is True
        assert "modified_payload" not in result

    @pytest.mark.asyncio
    async def test_agent_pre_invoke_with_user(self, plugin):
        """Test pre_invoke injects headers."""
        plugin._initialized = True

        context = {
            "user": {"email": "user@example.com"},
            "metadata": {
                "auth_method": "cognito",
                "customers": ["cloud-001", "cloud-002"],
            },
            "request_id": "req-123",
        }

        result = await plugin.agent_pre_invoke(
            {"headers": {"Existing": "header"}},
            context=context
        )

        assert result["continue_processing"] is True
        assert "modified_payload" in result

        headers = result["modified_payload"]["headers"]
        assert headers["Existing"] == "header"
        assert headers["X-User-Email"] == "user@example.com"
        assert headers["X-Request-ID"] == "req-123"

        customers = json.loads(headers["X-User-Customers"])
        assert "cloud-001" in customers
        assert "cloud-002" in customers

    @pytest.mark.asyncio
    async def test_agent_pre_invoke_disabled(self, plugin, test_settings):
        """Test pre_invoke when header propagation is disabled."""
        test_settings.enable_header_propagation = False
        plugin._settings = test_settings
        plugin._initialized = True

        context = {
            "user": {"email": "user@example.com"},
            "metadata": {"auth_method": "cognito", "customers": []},
        }

        result = await plugin.agent_pre_invoke({}, context=context)

        assert result["continue_processing"] is True
        assert "modified_payload" not in result


class TestCreatePlugin:
    """Tests for plugin factory function."""

    def test_create_plugin(self):
        """Test creating plugin via factory function."""
        from tcloud_cognito_auth.tcloud_cognito_auth import create_plugin

        plugin = create_plugin({"custom": "config"})

        assert isinstance(plugin, TCloudCognitoAuthPlugin)
        assert plugin._config == {"custom": "config"}

    def test_create_plugin_no_config(self):
        """Test creating plugin without config."""
        from tcloud_cognito_auth.tcloud_cognito_auth import create_plugin

        plugin = create_plugin()

        assert isinstance(plugin, TCloudCognitoAuthPlugin)
        assert plugin._config == {}
