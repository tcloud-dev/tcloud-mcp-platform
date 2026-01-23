"""TCloud Cognito Authentication Plugin for MCP Context Forge.

This plugin implements authentication via AWS Cognito JWT validation
and fetches user permissions from the TCloud API.
"""

import json
import logging
from typing import Any

# MCP Context Forge imports
try:
    from mcpgateway.plugins.framework.base import Plugin
    from mcpgateway.plugins.framework.models import PluginConfig, PluginContext, PluginResult
except ImportError:
    # Fallback for standalone testing
    Plugin = object
    PluginConfig = Any
    PluginContext = Any
    PluginResult = dict

from .cache import PermissionCache
from .cognito import CognitoJWTValidator
from .config import PluginSettings, get_settings
from .exceptions import (
    TCloudAPIError,
    TCloudAuthError,
    TokenExpiredError,
    TokenValidationError,
)
from .models import AuthenticatedUser, PropagatedHeaders
from .tcloud_api import TCloudAPIClient

logger = logging.getLogger(__name__)


class TCloudCognitoAuthPlugin(Plugin):
    """TCloud Cognito Authentication Plugin.

    Implements http_auth_resolve_user and agent_pre_invoke hooks for
    MCP Context Forge to provide JWT-based authentication with
    permission caching.
    """

    def __init__(self, config: PluginConfig):
        """Initialize the plugin.

        Args:
            config: Plugin configuration from Context Forge.
        """
        super().__init__(config)
        self._plugin_settings: PluginSettings | None = None
        self._cognito_validator: CognitoJWTValidator | None = None
        self._tcloud_client: TCloudAPIClient | None = None
        self._permission_cache: PermissionCache | None = None
        self._plugin_initialized = False

    @property
    def plugin_settings(self) -> PluginSettings:
        """Get plugin settings, loading from environment if needed."""
        if not self._plugin_settings:
            self._plugin_settings = get_settings()
        return self._plugin_settings

    async def initialize(self) -> None:
        """Initialize plugin resources.

        Called by Context Forge when the plugin is loaded.
        """
        if self._plugin_initialized:
            return

        logger.info("Initializing TCloud Cognito Auth Plugin")

        # Initialize components
        self._cognito_validator = CognitoJWTValidator(self.plugin_settings)
        await self._cognito_validator.initialize()

        self._tcloud_client = TCloudAPIClient(self.plugin_settings)
        await self._tcloud_client.initialize()

        self._permission_cache = PermissionCache(self.plugin_settings)
        await self._permission_cache.initialize()

        self._plugin_initialized = True
        logger.info("TCloud Cognito Auth Plugin initialized successfully")

    async def shutdown(self) -> None:
        """Clean up plugin resources.

        Called by Context Forge when the plugin is unloaded.
        """
        logger.info("Shutting down TCloud Cognito Auth Plugin")

        if self._cognito_validator:
            await self._cognito_validator.shutdown()
        if self._tcloud_client:
            await self._tcloud_client.shutdown()
        if self._permission_cache:
            await self._permission_cache.shutdown()

        self._plugin_initialized = False

    async def http_auth_resolve_user(
        self,
        payload: dict[str, Any],
        context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Resolve user from HTTP authentication credentials.

        This hook is called by Context Forge to authenticate incoming requests.
        It validates the Cognito JWT and fetches user permissions.

        Args:
            payload: Contains 'credentials' dict with auth info.
                - credentials.credentials: The Bearer token
                - credentials.scheme: The auth scheme (bearer)
            context: Optional context from Context Forge.

        Returns:
            Dict with:
                - modified_payload: User info for Context Forge
                - metadata: Additional info including permissions
                - continue_processing: Whether to continue auth chain
        """
        if not self._plugin_initialized:
            await self.initialize()

        # Extract credentials from payload (payload can be dict or HttpAuthResolveUserPayload object)
        if hasattr(payload, "credentials"):
            # Payload is an object with attributes
            creds_obj = payload.credentials
            token = getattr(creds_obj, "credentials", None)
            scheme = getattr(creds_obj, "scheme", "").lower()
        else:
            # Payload is a dict
            credentials = payload.get("credentials", {})
            token = credentials.get("credentials")
            scheme = credentials.get("scheme", "").lower()

        # Skip if no bearer token
        if not token or scheme != "bearer":
            logger.debug("No bearer token found, continuing auth chain")
            return {"continue_processing": True}

        try:
            # Validate JWT with Cognito
            claims = await self._cognito_validator.validate_token(token)
            email = claims.user_email

            logger.info(f"JWT validated for user: {email}")

            # Fetch permissions (with cache)
            async def fetch_permissions():
                return await self._tcloud_client.get_user_permissions(
                    email, bearer_token=token
                )

            permissions = await self._permission_cache.get_or_fetch(
                email, fetch_permissions
            )

            # Build authenticated user
            user = AuthenticatedUser(
                email=email,
                full_name=claims.name,
                cognito_sub=claims.sub,
                is_admin=False,
                is_active=True,
                customers=permissions.customers,
                roles=permissions.roles,
                permissions=permissions.permissions,
            )

            logger.info(
                f"Authenticated user {email} with {len(permissions.customers)} customers"
            )

            return {
                "modified_payload": user.to_gateway_user(),
                "metadata": user.to_metadata(),
                "continue_processing": True,
            }

        except TokenExpiredError as e:
            logger.warning(f"Token expired: {e}")
            return {
                "error": {
                    "message": "Token expired",
                    "code": "TOKEN_EXPIRED",
                },
                "continue_processing": False,
            }

        except TokenValidationError as e:
            logger.warning(f"Token validation failed: {e}")
            return {
                "error": {
                    "message": str(e),
                    "code": e.code,
                },
                "continue_processing": False,
            }

        except TCloudAPIError as e:
            logger.error(f"TCloud API error: {e}")
            # Continue with basic auth if API fails
            return {"continue_processing": True}

        except Exception as e:
            logger.error(f"Unexpected auth error: {e}", exc_info=True)
            return {"continue_processing": True}

    async def agent_pre_invoke(
        self,
        payload: dict[str, Any],
        context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Inject user context headers before agent invocation.

        This hook is called before each agent request to inject
        user identity headers that agents can use for authorization.

        Args:
            payload: Contains request info including headers.
            context: Context with authenticated user info.

        Returns:
            Dict with:
                - modified_payload: Updated payload with injected headers
                - continue_processing: Always True to continue
        """
        if not self.plugin_settings.enable_header_propagation:
            return {"continue_processing": True}

        # Get user info from context
        user_metadata = (context or {}).get("metadata", {})
        if not user_metadata or user_metadata.get("auth_method") != "cognito":
            return {"continue_processing": True}

        user_email = (context or {}).get("user", {}).get("email")
        if not user_email:
            return {"continue_processing": True}

        # Build headers to inject
        customers = user_metadata.get("customers", [])
        headers_to_inject = {
            "X-User-Email": user_email,
            "X-User-Customers": json.dumps(customers),
        }

        # Get existing headers from payload
        existing_headers = payload.get("headers", {})
        merged_headers = {**existing_headers, **headers_to_inject}

        # Get request ID if available
        request_id = (context or {}).get("request_id")
        if request_id:
            merged_headers["X-Request-ID"] = request_id

        logger.debug(
            f"Injecting headers for {user_email}: "
            f"X-User-Customers={len(customers)} customers"
        )

        return {
            "modified_payload": {**payload, "headers": merged_headers},
            "continue_processing": True,
        }

    async def tool_pre_invoke(
        self,
        payload: dict[str, Any],
        context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Inject user context before tool invocation.

        Similar to agent_pre_invoke but for tool calls.

        Args:
            payload: Tool invocation payload.
            context: Context with authenticated user info.

        Returns:
            Dict with modified payload including user context.
        """
        # Reuse the same logic as agent_pre_invoke
        return await self.agent_pre_invoke(payload, context)


# Plugin factory function for Context Forge
def create_plugin(config: dict[str, Any] | None = None) -> TCloudCognitoAuthPlugin:
    """Create a new plugin instance.

    Args:
        config: Configuration from Context Forge.

    Returns:
        Configured plugin instance.
    """
    return TCloudCognitoAuthPlugin(config)
