"""TCloud API client for user permissions."""

import logging
from typing import Any

import httpx

from .config import PluginSettings
from .exceptions import TCloudAPIError
from .models import UserPermissions

logger = logging.getLogger(__name__)


class TCloudAPIClient:
    """Client for TCloud API to fetch user permissions."""

    def __init__(self, settings: PluginSettings):
        """Initialize the TCloud API client.

        Args:
            settings: Plugin configuration settings.
        """
        self.settings = settings
        self._http_client: httpx.AsyncClient | None = None

    async def initialize(self) -> None:
        """Initialize the HTTP client."""
        self._http_client = httpx.AsyncClient(
            base_url=self.settings.tcloud_api_url,
            timeout=30.0,
            headers={
                "x-api-key": self.settings.tcloud_api_key,
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
        )

    async def shutdown(self) -> None:
        """Clean up resources."""
        if self._http_client:
            await self._http_client.aclose()
            self._http_client = None

    async def get_user_permissions(
        self, email: str, bearer_token: str | None = None
    ) -> UserPermissions:
        """Fetch user permissions from TCloud API.

        Args:
            email: User email address.
            bearer_token: Optional Bearer token to forward to API.

        Returns:
            UserPermissions object with user's permissions.

        Raises:
            TCloudAPIError: If API request fails.
        """
        if not self._http_client:
            await self.initialize()

        headers = {}
        if bearer_token:
            headers["Authorization"] = f"Bearer {bearer_token}"

        try:
            # Try /customer endpoint first (main source of permissions)
            response = await self._http_client.get("/customer", headers=headers)

            if response.status_code == 200:
                data = response.json()
                customers = self._extract_customers(data)
                return UserPermissions(
                    email=email,
                    customers=customers,
                    roles=self._extract_roles(data),
                    permissions=self._extract_permissions(data),
                )
            elif response.status_code == 401:
                raise TCloudAPIError(
                    "Unauthorized access to TCloud API", status_code=401
                )
            elif response.status_code == 403:
                # User authenticated but has no permissions
                logger.warning(f"User {email} has no customer permissions")
                return UserPermissions(email=email, customers=[], roles=[], permissions=[])
            else:
                raise TCloudAPIError(
                    f"TCloud API error: {response.status_code} - {response.text}",
                    status_code=response.status_code,
                )

        except httpx.TimeoutException as e:
            raise TCloudAPIError(f"TCloud API timeout: {e}")
        except httpx.HTTPError as e:
            raise TCloudAPIError(f"TCloud API request failed: {e}")

    async def get_user_profile(
        self, email: str, bearer_token: str | None = None
    ) -> dict[str, Any]:
        """Fetch user profile from TCloud API.

        Args:
            email: User email address.
            bearer_token: Optional Bearer token to forward to API.

        Returns:
            User profile data.

        Raises:
            TCloudAPIError: If API request fails.
        """
        if not self._http_client:
            await self.initialize()

        headers = {}
        if bearer_token:
            headers["Authorization"] = f"Bearer {bearer_token}"

        try:
            response = await self._http_client.get("/user/profile", headers=headers)

            if response.status_code == 200:
                return response.json()
            elif response.status_code == 404:
                return {"email": email, "name": email}
            else:
                logger.warning(
                    f"Failed to fetch profile for {email}: {response.status_code}"
                )
                return {"email": email, "name": email}

        except httpx.HTTPError as e:
            logger.warning(f"Failed to fetch user profile: {e}")
            return {"email": email, "name": email}

    def _extract_customers(self, data: Any) -> list[str]:
        """Extract customer/cloud IDs from API response.

        Args:
            data: API response data.

        Returns:
            List of customer/cloud IDs.
        """
        customers = []

        if isinstance(data, list):
            # Response is a list of customer objects
            for item in data:
                if isinstance(item, dict):
                    cloud_id = item.get("cloud_id") or item.get("cloudId") or item.get("id")
                    if cloud_id:
                        customers.append(str(cloud_id))
        elif isinstance(data, dict):
            # Response might have a customers/data array
            items = data.get("customers") or data.get("data") or []
            for item in items:
                if isinstance(item, dict):
                    cloud_id = item.get("cloud_id") or item.get("cloudId") or item.get("id")
                    if cloud_id:
                        customers.append(str(cloud_id))

        return customers

    def _extract_roles(self, data: Any) -> list[str]:
        """Extract user roles from API response.

        Args:
            data: API response data.

        Returns:
            List of role names.
        """
        roles = set()

        if isinstance(data, list):
            for item in data:
                if isinstance(item, dict):
                    role = item.get("role") or item.get("permission_level")
                    if role:
                        roles.add(str(role))
        elif isinstance(data, dict):
            user_roles = data.get("roles") or []
            roles.update(str(r) for r in user_roles if r)

        return list(roles)

    def _extract_permissions(self, data: Any) -> list[str]:
        """Extract specific permissions from API response.

        Args:
            data: API response data.

        Returns:
            List of permission strings.
        """
        permissions = set()

        # Default read permissions if user has any customers
        if isinstance(data, list) and len(data) > 0:
            permissions.add("read:metrics")
            permissions.add("read:logs")

        if isinstance(data, dict):
            user_perms = data.get("permissions") or []
            permissions.update(str(p) for p in user_perms if p)

        return list(permissions)
