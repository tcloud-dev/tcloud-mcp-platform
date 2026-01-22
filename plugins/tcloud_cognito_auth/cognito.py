"""AWS Cognito JWT validation for TCloud Auth Plugin."""

import time
from typing import Any

import httpx
from jose import jwt, JWTError
from jose.exceptions import ExpiredSignatureError, JWTClaimsError

from .config import PluginSettings
from .exceptions import (
    InvalidAudienceError,
    InvalidIssuerError,
    InvalidSignatureError,
    JWKSFetchError,
    KeyNotFoundError,
    TokenExpiredError,
    TokenValidationError,
)
from .models import CognitoClaims


class CognitoJWTValidator:
    """Validates JWT tokens issued by AWS Cognito."""

    def __init__(self, settings: PluginSettings):
        """Initialize the validator with settings.

        Args:
            settings: Plugin configuration settings.
        """
        self.settings = settings
        self._jwks_cache: dict[str, Any] | None = None
        self._jwks_cache_time: float = 0
        self._http_client: httpx.AsyncClient | None = None

    async def initialize(self) -> None:
        """Initialize the HTTP client and pre-fetch JWKS."""
        self._http_client = httpx.AsyncClient(timeout=10.0)
        await self._refresh_jwks()

    async def shutdown(self) -> None:
        """Clean up resources."""
        if self._http_client:
            await self._http_client.aclose()
            self._http_client = None

    async def validate_token(self, token: str) -> CognitoClaims:
        """Validate a Cognito JWT token.

        Args:
            token: The JWT token string (without 'Bearer ' prefix).

        Returns:
            Parsed and validated token claims.

        Raises:
            TokenValidationError: If token validation fails.
            TokenExpiredError: If token has expired.
            InvalidSignatureError: If signature verification fails.
            InvalidIssuerError: If issuer is invalid.
            InvalidAudienceError: If audience/client_id is invalid.
        """
        try:
            # Get the key ID from the token header
            unverified_header = jwt.get_unverified_header(token)
            kid = unverified_header.get("kid")

            if not kid:
                raise TokenValidationError("Token header missing 'kid'")

            # Get the signing key from JWKS
            signing_key = await self._get_signing_key(kid)

            # Decode and validate the token
            claims = jwt.decode(
                token,
                signing_key,
                algorithms=["RS256"],
                issuer=self.settings.cognito_issuer,
                options={
                    "verify_aud": False,  # We'll verify client_id manually for access tokens
                    "leeway": self.settings.clock_skew_tolerance,
                },
            )

            # Parse claims into model
            parsed_claims = CognitoClaims(**claims)

            # Validate client_id for access tokens
            if parsed_claims.token_use == "access":
                if parsed_claims.client_id != self.settings.cognito_app_client_id:
                    raise InvalidAudienceError(
                        f"Invalid client_id: {parsed_claims.client_id}"
                    )

            return parsed_claims

        except ExpiredSignatureError as e:
            raise TokenExpiredError(str(e))
        except JWTClaimsError as e:
            if "issuer" in str(e).lower():
                raise InvalidIssuerError(str(e))
            raise TokenValidationError(str(e))
        except JWTError as e:
            error_msg = str(e).lower()
            if "signature" in error_msg:
                raise InvalidSignatureError(str(e))
            raise TokenValidationError(str(e))

    async def _get_signing_key(self, kid: str) -> dict[str, Any]:
        """Get the signing key from JWKS by key ID.

        Args:
            kid: The key ID from the JWT header.

        Returns:
            The JWK for the given key ID.

        Raises:
            KeyNotFoundError: If key is not found in JWKS.
        """
        jwks = await self._get_jwks()

        for key in jwks.get("keys", []):
            if key.get("kid") == kid:
                return key

        # Key not found, try refreshing JWKS (key rotation may have occurred)
        await self._refresh_jwks()
        jwks = self._jwks_cache

        for key in jwks.get("keys", []):
            if key.get("kid") == kid:
                return key

        raise KeyNotFoundError(f"Key with kid '{kid}' not found in JWKS")

    async def _get_jwks(self) -> dict[str, Any]:
        """Get JWKS, using cache if available and not expired.

        Returns:
            The JWKS dictionary.
        """
        now = time.time()
        cache_age = now - self._jwks_cache_time

        if self._jwks_cache and cache_age < self.settings.jwks_cache_ttl:
            return self._jwks_cache

        await self._refresh_jwks()
        return self._jwks_cache

    async def _refresh_jwks(self) -> None:
        """Fetch fresh JWKS from Cognito.

        Raises:
            JWKSFetchError: If JWKS cannot be fetched.
        """
        if not self._http_client:
            self._http_client = httpx.AsyncClient(timeout=10.0)

        try:
            response = await self._http_client.get(self.settings.cognito_jwks_url)
            response.raise_for_status()
            self._jwks_cache = response.json()
            self._jwks_cache_time = time.time()
        except httpx.HTTPError as e:
            # If we have cached JWKS, use it as fallback
            if self._jwks_cache:
                return
            raise JWKSFetchError(f"Failed to fetch JWKS: {e}")

    def extract_token_from_header(self, auth_header: str | None) -> str | None:
        """Extract Bearer token from Authorization header.

        Args:
            auth_header: The Authorization header value.

        Returns:
            The token string, or None if not found/invalid.
        """
        if not auth_header:
            return None

        parts = auth_header.split()
        if len(parts) != 2 or parts[0].lower() != "bearer":
            return None

        return parts[1]
