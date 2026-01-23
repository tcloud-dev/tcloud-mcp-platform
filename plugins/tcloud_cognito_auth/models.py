"""Data models for TCloud Cognito Auth Plugin."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class CognitoClaims(BaseModel):
    """Parsed claims from a Cognito JWT token."""

    sub: str = Field(..., description="Subject (unique user ID)")
    iss: str = Field(..., description="Issuer URL")
    token_use: str = Field(..., description="Token use (access or id)")
    exp: int = Field(..., description="Expiration timestamp")
    iat: int = Field(..., description="Issued at timestamp")
    client_id: str | None = Field(None, description="Client ID (for access tokens)")
    username: str | None = Field(None, description="Username")
    email: str | None = Field(None, description="User email (for id tokens)")
    name: str | None = Field(None, description="User full name")

    @property
    def user_email(self) -> str:
        """Extract user email from claims."""
        if self.email:
            return self.email
        # For access tokens, extract email from username (format: provider_email)
        if self.username and "_" in self.username:
            return self.username.split("_", 1)[1]
        return self.username or self.sub


class UserPermissions(BaseModel):
    """User permissions fetched from TCloud API."""

    email: str = Field(..., description="User email")
    customers: list[str] = Field(
        default_factory=list, description="List of customer/cloud IDs"
    )
    roles: list[str] = Field(default_factory=list, description="User roles")
    permissions: list[str] = Field(
        default_factory=list, description="Specific permissions"
    )
    fetched_at: datetime = Field(
        default_factory=datetime.utcnow, description="When permissions were fetched"
    )

    def to_cache_dict(self) -> dict[str, Any]:
        """Convert to dictionary for caching."""
        return {
            "email": self.email,
            "customers": self.customers,
            "roles": self.roles,
            "permissions": self.permissions,
            "fetched_at": self.fetched_at.isoformat(),
        }

    @classmethod
    def from_cache_dict(cls, data: dict[str, Any]) -> "UserPermissions":
        """Create from cached dictionary."""
        if isinstance(data.get("fetched_at"), str):
            data["fetched_at"] = datetime.fromisoformat(data["fetched_at"])
        return cls(**data)


class AuthenticatedUser(BaseModel):
    """Represents an authenticated user with permissions."""

    email: str = Field(..., description="User email")
    full_name: str | None = Field(None, description="User full name")
    cognito_sub: str = Field(..., description="Cognito subject ID")
    is_admin: bool = Field(default=False, description="Whether user is admin")
    is_active: bool = Field(default=True, description="Whether user is active")
    customers: list[str] = Field(
        default_factory=list, description="Allowed customer IDs"
    )
    roles: list[str] = Field(default_factory=list, description="User roles")
    permissions: list[str] = Field(default_factory=list, description="User permissions")
    auth_method: str = Field(default="cognito", description="Authentication method")

    def to_gateway_user(self) -> dict[str, Any]:
        """Convert to Context Forge user format."""
        return {
            "email": self.email,
            "full_name": self.full_name or self.email,
            "is_admin": self.is_admin,
            "is_active": self.is_active,
        }

    def to_metadata(self) -> dict[str, Any]:
        """Convert to metadata for header propagation."""
        return {
            "auth_method": self.auth_method,
            "cognito_sub": self.cognito_sub,
            "customers": self.customers,
            "roles": self.roles,
            "permissions": self.permissions,
        }


class PropagatedHeaders(BaseModel):
    """Headers to propagate to downstream agents."""

    x_user_email: str = Field(..., alias="X-User-Email")
    x_user_customers: str = Field(..., alias="X-User-Customers")
    x_request_id: str | None = Field(None, alias="X-Request-ID")

    model_config = {"populate_by_name": True}

    @classmethod
    def from_authenticated_user(
        cls, user: AuthenticatedUser, request_id: str | None = None
    ) -> "PropagatedHeaders":
        """Create headers from authenticated user."""
        import json

        return cls(
            **{
                "X-User-Email": user.email,
                "X-User-Customers": json.dumps(user.customers),
                "X-Request-ID": request_id,
            }
        )
