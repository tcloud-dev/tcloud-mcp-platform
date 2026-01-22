"""Configuration management for TCloud Cognito Auth Plugin."""

from pydantic import Field
from pydantic_settings import BaseSettings


class PluginSettings(BaseSettings):
    """Plugin configuration loaded from environment variables."""

    # Cognito settings
    cognito_user_pool_id: str = Field(
        ...,
        description="AWS Cognito User Pool ID",
    )
    cognito_region: str = Field(
        default="us-east-2",
        description="AWS region for Cognito",
    )
    cognito_app_client_id: str = Field(
        ...,
        description="Cognito App Client ID for audience validation",
    )

    # TCloud API settings
    tcloud_api_url: str = Field(
        ...,
        description="TCloud API base URL",
    )
    tcloud_api_key: str = Field(
        ...,
        description="TCloud API authentication key",
    )

    # Cache settings
    redis_url: str = Field(
        default="redis://localhost:6379/0",
        description="Redis connection URL",
    )
    permission_cache_ttl: int = Field(
        default=300,
        description="Permission cache TTL in seconds",
    )

    # JWKS cache settings
    jwks_cache_ttl: int = Field(
        default=3600,
        description="JWKS cache TTL in seconds (1 hour)",
    )

    # Plugin behavior
    enable_header_propagation: bool = Field(
        default=True,
        description="Enable header propagation to downstream agents",
    )
    clock_skew_tolerance: int = Field(
        default=300,
        description="Clock skew tolerance in seconds for token validation",
    )

    model_config = {
        "env_prefix": "",
        "case_sensitive": False,
        "extra": "ignore",
    }

    @property
    def cognito_issuer(self) -> str:
        """Get the Cognito issuer URL."""
        return f"https://cognito-idp.{self.cognito_region}.amazonaws.com/{self.cognito_user_pool_id}"

    @property
    def cognito_jwks_url(self) -> str:
        """Get the Cognito JWKS URL."""
        return f"{self.cognito_issuer}/.well-known/jwks.json"


def get_settings() -> PluginSettings:
    """Get plugin settings from environment variables."""
    return PluginSettings()
