"""TCloud Cognito Authentication Plugin for MCP Context Forge.

This plugin provides:
- JWT validation via AWS Cognito
- User permissions fetching from TCloud API
- Redis caching for permissions
- Header propagation to downstream agents
"""

__version__ = "1.0.0"
__author__ = "TCloud Platform Team"

from .tcloud_cognito_auth import TCloudCognitoAuthPlugin

__all__ = ["TCloudCognitoAuthPlugin"]
