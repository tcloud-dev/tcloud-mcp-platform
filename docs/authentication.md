# Authentication Architecture

This document describes the authentication architecture for the TCloud MCP Platform.

## Overview

Authentication is handled centrally at the **MCP Context Forge gateway**, which validates JWT tokens from AWS Cognito and propagates user context to downstream MCP agents.

## Authentication Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           AUTHENTICATION FLOW                                │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────┐      OAuth 2.1        ┌──────────────────────────────────┐    │
│  │ Client  │  (Cognito + Fluig)    │       MCP Context Forge          │    │
│  │         ├──────────────────────►│                                  │    │
│  └─────────┘                       │  1. Validates JWT (Cognito)      │    │
│                                    │  2. Fetches permissions (TCloud) │    │
│                                    │  3. Caches in Redis              │    │
│                                    │  4. Propagates headers to agents │    │
│                                    └───────────────┬──────────────────┘    │
│                                                    │                       │
│                              Headers propagated:   │                       │
│                              • X-User-Email        │                       │
│                              • X-User-Customers    │                       │
│                                                    ▼                       │
│                                    ┌──────────────────────────────────┐    │
│                                    │      Orchestrator Agent          │    │
│                                    └───────────────┬──────────────────┘    │
│                                                    │                       │
│                    ┌───────────────┬───────────────┴───────────────┐       │
│                    ▼               ▼                               ▼       │
│              ┌──────────┐   ┌──────────┐                    ┌──────────┐   │
│              │ CPU/RAM  │   │    DB    │        ...         │   App    │   │
│              │  Agent   │   │  Agent   │                    │  Agent   │   │
│              └──────────┘   └──────────┘                    └──────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Components

### 1. AWS Cognito

- **Purpose**: Identity provider for user authentication
- **Token Type**: JWT (access tokens and ID tokens)
- **Region**: us-east-2
- **Integration**: OAuth 2.1 with Fluig Identity

### 2. TCloud Cognito Auth Plugin

Custom plugin for MCP Context Forge that:

1. **Validates JWTs** using Cognito JWKS (with caching)
2. **Fetches Permissions** from TCloud API
3. **Caches Permissions** in Redis (5 min TTL)
4. **Propagates Headers** to downstream agents

See [Plugin README](../plugins/tcloud_cognito_auth/README.md) for details.

### 3. TCloud API

- **Endpoint**: `/customer`
- **Returns**: List of customer/cloud IDs the user can access
- **Authentication**: Bearer token + API key

### 4. Redis Cache

- **Purpose**: Cache user permissions to reduce API calls
- **TTL**: 5 minutes (configurable)
- **Key Pattern**: `tcloud:auth:permissions:{email_hash}`

## Propagated Headers

Headers injected by the plugin for downstream agents:

| Header | Description | Example |
|--------|-------------|---------|
| `X-User-Email` | Authenticated user's email | `user@totvs.com.br` |
| `X-User-Customers` | JSON array of cloud_ids | `["cloud-001", "cloud-002"]` |
| `X-Request-ID` | Request correlation ID | `uuid` |

## Agent Authorization

Agents should use propagated headers for authorization:

```python
import json

async def check_authorization(request, cloud_id: str):
    """Check if user can access the given cloud."""
    user_email = request.headers.get("X-User-Email")
    customers_json = request.headers.get("X-User-Customers", "[]")
    user_customers = json.loads(customers_json)
    
    if cloud_id not in user_customers:
        raise PermissionError(
            f"User {user_email} cannot access cloud {cloud_id}"
        )
```

## Dual-Mode Authentication

Agents support two authentication modes:

### 1. Via Gateway (Recommended)

When called through Context Forge, agents receive pre-validated headers:

```python
user_email = request.headers.get("X-User-Email")
# Already validated by gateway - safe to use
```

### 2. Standalone Mode

When agents are accessed directly, they validate JWT themselves:

```python
async def authenticate(request):
    # Check for gateway headers first
    if "X-User-Email" in request.headers:
        return GatewayAuth(request.headers)
    
    # Fallback to direct JWT validation
    auth_header = request.headers.get("Authorization")
    if auth_header:
        return await validate_jwt(auth_header)
    
    raise Unauthorized()
```

## Configuration

### Environment Variables

```bash
# Cognito
COGNITO_USER_POOL_ID=sa-east-1_xxx
COGNITO_REGION=us-east-2
COGNITO_APP_CLIENT_ID=xxx

# TCloud API
TCLOUD_API_URL=https://api.tcloud.cloudtotvs.com.br/dev
TCLOUD_API_KEY=xxx

# Cache
REDIS_URL=redis://redis:6379/0
PERMISSION_CACHE_TTL=300
```

### Kubernetes Secret

```bash
kubectl create secret generic tcloud-cognito-auth-secret \
  --from-literal=COGNITO_USER_POOL_ID=sa-east-1_xxx \
  --from-literal=COGNITO_REGION=us-east-2 \
  --from-literal=COGNITO_APP_CLIENT_ID=xxx \
  --from-literal=TCLOUD_API_URL=https://api.tcloud.cloudtotvs.com.br/dev \
  --from-literal=TCLOUD_API_KEY=xxx \
  -n mcp-dev
```

## Security Considerations

1. **Token Validation**: Full JWT validation including signature, issuer, audience, and expiration
2. **Secrets Management**: All credentials stored in Kubernetes Secrets
3. **Cache Security**: Redis should use authentication and TLS in production
4. **Header Trust**: Agents should validate that requests come from known gateway IPs
5. **Audit Logging**: All authentication events are logged

## Troubleshooting

### Token Expired

```json
{
  "error": {
    "code": "TOKEN_EXPIRED",
    "message": "Token has expired"
  }
}
```

**Solution**: Client needs to refresh the access token.

### Invalid Token

```json
{
  "error": {
    "code": "INVALID_TOKEN",
    "message": "Invalid token signature"
  }
}
```

**Solution**: Verify the token was issued by the correct Cognito User Pool.

### Permission Denied

```json
{
  "error": {
    "code": "FORBIDDEN",
    "message": "User does not have access to this cloud"
  }
}
```

**Solution**: Verify user has the correct permissions in TCloud.

## References

- [AWS Cognito JWT Verification](https://docs.aws.amazon.com/cognito/latest/developerguide/amazon-cognito-user-pools-using-tokens-verifying-a-jwt.html)
- [MCP Context Forge Plugin Framework](https://github.com/IBM/mcp-context-forge)
- [TCloud API Documentation](https://api.tcloud.cloudtotvs.com.br/docs)
