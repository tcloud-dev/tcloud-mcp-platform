"""Custom exceptions for TCloud Cognito Auth Plugin."""


class TCloudAuthError(Exception):
    """Base exception for TCloud authentication errors."""

    def __init__(self, message: str, code: str = "AUTH_ERROR"):
        self.message = message
        self.code = code
        super().__init__(self.message)


class TokenValidationError(TCloudAuthError):
    """Raised when JWT token validation fails."""

    def __init__(self, message: str, code: str = "INVALID_TOKEN"):
        super().__init__(message, code)


class TokenExpiredError(TokenValidationError):
    """Raised when JWT token has expired."""

    def __init__(self, message: str = "Token has expired"):
        super().__init__(message, "TOKEN_EXPIRED")


class InvalidSignatureError(TokenValidationError):
    """Raised when JWT signature is invalid."""

    def __init__(self, message: str = "Invalid token signature"):
        super().__init__(message, "INVALID_SIGNATURE")


class InvalidIssuerError(TokenValidationError):
    """Raised when JWT issuer is invalid."""

    def __init__(self, message: str = "Invalid token issuer"):
        super().__init__(message, "INVALID_ISSUER")


class InvalidAudienceError(TokenValidationError):
    """Raised when JWT audience is invalid."""

    def __init__(self, message: str = "Invalid token audience"):
        super().__init__(message, "INVALID_AUDIENCE")


class JWKSFetchError(TCloudAuthError):
    """Raised when JWKS cannot be fetched."""

    def __init__(self, message: str = "Failed to fetch JWKS"):
        super().__init__(message, "JWKS_FETCH_ERROR")


class KeyNotFoundError(TCloudAuthError):
    """Raised when signing key is not found in JWKS."""

    def __init__(self, message: str = "Signing key not found in JWKS"):
        super().__init__(message, "KEY_NOT_FOUND")


class TCloudAPIError(TCloudAuthError):
    """Raised when TCloud API request fails."""

    def __init__(self, message: str, status_code: int | None = None):
        self.status_code = status_code
        code = f"TCLOUD_API_ERROR_{status_code}" if status_code else "TCLOUD_API_ERROR"
        super().__init__(message, code)


class CacheError(TCloudAuthError):
    """Raised when cache operations fail."""

    def __init__(self, message: str = "Cache operation failed"):
        super().__init__(message, "CACHE_ERROR")
