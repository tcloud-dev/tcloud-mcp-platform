"""Tests for TCloud API client."""

from unittest.mock import AsyncMock, MagicMock

import httpx
import pytest

from tcloud_cognito_auth.exceptions import TCloudAPIError
from tcloud_cognito_auth.tcloud_api import TCloudAPIClient


@pytest.fixture
def api_client(test_settings):
    """Create an API client instance."""
    return TCloudAPIClient(test_settings)


class TestTCloudAPIClient:
    """Tests for TCloudAPIClient."""

    @pytest.mark.asyncio
    async def test_initialize_and_shutdown(self, api_client):
        """Test client initialization and shutdown."""
        await api_client.initialize()
        assert api_client._http_client is not None

        await api_client.shutdown()
        assert api_client._http_client is None

    @pytest.mark.asyncio
    async def test_get_user_permissions_success(
        self, api_client, sample_user_permissions
    ):
        """Test successful permission fetch."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            {"cloud_id": "cloud-001", "role": "viewer"},
            {"cloud_id": "cloud-002", "role": "operator"},
            {"cloud_id": "cloud-003", "role": "viewer"},
        ]

        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_response)
        api_client._http_client = mock_client

        permissions = await api_client.get_user_permissions("user@example.com")

        assert permissions.email == "user@example.com"
        assert "cloud-001" in permissions.customers
        assert "cloud-002" in permissions.customers
        assert "cloud-003" in permissions.customers

    @pytest.mark.asyncio
    async def test_get_user_permissions_unauthorized(self, api_client):
        """Test unauthorized response."""
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_response.text = "Unauthorized"

        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_response)
        api_client._http_client = mock_client

        with pytest.raises(TCloudAPIError) as exc_info:
            await api_client.get_user_permissions("user@example.com")

        assert exc_info.value.status_code == 401

    @pytest.mark.asyncio
    async def test_get_user_permissions_forbidden(self, api_client):
        """Test forbidden response (no permissions)."""
        mock_response = MagicMock()
        mock_response.status_code = 403
        mock_response.text = "Forbidden"

        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_response)
        api_client._http_client = mock_client

        permissions = await api_client.get_user_permissions("user@example.com")

        assert permissions.email == "user@example.com"
        assert permissions.customers == []

    @pytest.mark.asyncio
    async def test_get_user_permissions_timeout(self, api_client):
        """Test timeout handling."""
        mock_client = AsyncMock()
        mock_client.get = AsyncMock(side_effect=httpx.TimeoutException("Timeout"))
        api_client._http_client = mock_client

        with pytest.raises(TCloudAPIError, match="timeout"):
            await api_client.get_user_permissions("user@example.com")

    @pytest.mark.asyncio
    async def test_get_user_permissions_with_bearer_token(self, api_client):
        """Test passing bearer token to API."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = []

        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_response)
        api_client._http_client = mock_client

        await api_client.get_user_permissions(
            "user@example.com", bearer_token="test-token"
        )

        # Verify Authorization header was passed
        call_args = mock_client.get.call_args
        assert call_args[1]["headers"]["Authorization"] == "Bearer test-token"


class TestExtractMethods:
    """Tests for data extraction methods."""

    @pytest.fixture
    def client(self, test_settings):
        """Create a client instance."""
        return TCloudAPIClient(test_settings)

    def test_extract_customers_from_list(self, client):
        """Test extracting customers from list response."""
        data = [
            {"cloud_id": "cloud-001"},
            {"cloud_id": "cloud-002"},
            {"cloudId": "cloud-003"},
            {"id": "cloud-004"},
        ]
        customers = client._extract_customers(data)
        assert set(customers) == {"cloud-001", "cloud-002", "cloud-003", "cloud-004"}

    def test_extract_customers_from_dict(self, client):
        """Test extracting customers from dict response."""
        data = {
            "customers": [
                {"cloud_id": "cloud-001"},
                {"cloud_id": "cloud-002"},
            ]
        }
        customers = client._extract_customers(data)
        assert set(customers) == {"cloud-001", "cloud-002"}

    def test_extract_roles(self, client):
        """Test extracting roles."""
        data = [
            {"cloud_id": "cloud-001", "role": "viewer"},
            {"cloud_id": "cloud-002", "role": "operator"},
            {"cloud_id": "cloud-003", "role": "viewer"},
        ]
        roles = client._extract_roles(data)
        assert set(roles) == {"viewer", "operator"}

    def test_extract_permissions_default(self, client):
        """Test default permissions for users with customers."""
        data = [{"cloud_id": "cloud-001"}]
        permissions = client._extract_permissions(data)
        assert "read:metrics" in permissions
        assert "read:logs" in permissions

    def test_extract_permissions_empty(self, client):
        """Test no default permissions for empty customer list."""
        permissions = client._extract_permissions([])
        assert permissions == []
