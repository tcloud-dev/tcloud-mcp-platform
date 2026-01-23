# TCloud Cognito Auth Plugin

Authentication plugin for MCP Context Forge that validates AWS Cognito JWTs and fetches user permissions from the TCloud API.

## Features

- **JWT Validation**: Validates tokens against Cognito JWKS with caching
- **Permission Caching**: Redis-based caching (5 min TTL) for user permissions
- **TCloud API Integration**: Fetches customer/cloud permissions from TCloud API
- **Header Propagation**: Injects `X-User-Email` and `X-User-Customers` headers for downstream agents

## Architecture

```
[Client + JWT] → [Context Forge] → [TCloud Cognito Auth Plugin]
                                           │
                      ┌────────────────────┼────────────────────┐
                      ↓                    ↓                    ↓
              [Cognito JWKS]        [Redis Cache]        [TCloud API]
                      │                    │                    │
                      └────────────────────┼────────────────────┘
                                           ↓
                                   [Authenticated User]
                                           ↓
                              [Header Injection to Agents]
```

## Hooks Implemented

| Hook | Purpose |
|------|---------|
| `http_auth_resolve_user` | Validates JWT, fetches permissions, returns user info |
| `agent_pre_invoke` | Injects user headers before agent calls |
| `tool_pre_invoke` | Injects user headers before tool calls |

## Configuration

### Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `COGNITO_USER_POOL_ID` | Yes | - | Cognito User Pool ID |
| `COGNITO_REGION` | No | `us-east-2` | AWS region |
| `COGNITO_APP_CLIENT_ID` | Yes | - | Cognito App Client ID |
| `TCLOUD_API_URL` | Yes | - | TCloud API base URL |
| `TCLOUD_API_KEY` | Yes | - | TCloud API key |
| `REDIS_URL` | No | `redis://localhost:6379/0` | Redis connection URL |
| `PERMISSION_CACHE_TTL` | No | `300` | Cache TTL in seconds |
| `JWKS_CACHE_TTL` | No | `3600` | JWKS cache TTL in seconds |

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

## Propagated Headers

Headers injected to downstream agents:

| Header | Description | Example |
|--------|-------------|---------|
| `X-User-Email` | Authenticated user's email | `user@example.com` |
| `X-User-Customers` | JSON array of customer IDs | `["cloud-001", "cloud-002"]` |
| `X-Request-ID` | Request tracking ID | `uuid` |

## Development

### Install Dependencies

```bash
pip install -r requirements.txt
```

### Run Tests

```bash
pytest tests/ -v
```

### Run Tests with Coverage

```bash
pytest tests/ -v --cov=. --cov-report=html
```

## Deployment

### Build ConfigMap

```bash
make build-plugin-configmap
```

### Deploy to Kubernetes

```bash
# Create secret (one-time)
make create-auth-secret \
  COGNITO_USER_POOL_ID=sa-east-1_xxx \
  COGNITO_APP_CLIENT_ID=xxx \
  TCLOUD_API_URL=https://api.tcloud.cloudtotvs.com.br/dev \
  TCLOUD_API_KEY=xxx \
  ENV=dev

# Deploy ConfigMap
make deploy-plugin-configmap ENV=dev

# Redeploy Context Forge to pick up changes
make deploy-context-forge ENV=dev
```

## Agent Integration

Agents can read propagated headers to get user context:

```python
async def handle_request(request):
    user_email = request.headers.get("X-User-Email")
    user_customers_json = request.headers.get("X-User-Customers", "[]")
    user_customers = json.loads(user_customers_json)
    
    # Use for authorization
    if requested_cloud_id not in user_customers:
        raise PermissionDenied("Access denied to this cloud")
```

## Dual-Mode Support

Agents can work both via Context Forge (using headers) and standalone (validating JWT directly):

```python
async def get_user_context(request):
    # Try headers first (via gateway)
    user_email = request.headers.get("X-User-Email")
    if user_email:
        return {
            "email": user_email,
            "customers": json.loads(request.headers.get("X-User-Customers", "[]"))
        }
    
    # Fallback: validate JWT directly (standalone mode)
    auth_header = request.headers.get("Authorization")
    if auth_header:
        return await validate_jwt_standalone(auth_header)
    
    return None
```

## Troubleshooting

### Common Issues

**JWKS Fetch Error**
- Check network connectivity to Cognito
- Verify `COGNITO_USER_POOL_ID` and `COGNITO_REGION` are correct

**Token Expired**
- Client needs to refresh the token
- Check `clock_skew_tolerance` setting

**TCloud API Error**
- Verify `TCLOUD_API_URL` and `TCLOUD_API_KEY`
- Check API connectivity

**Cache Issues**
- Verify Redis connectivity
- Check `REDIS_URL` configuration

### Debug Mode

Enable debug logging:

```yaml
mcpContextForge:
  config:
    LOG_LEVEL: DEBUG
```

## License

Proprietary - TCloud Platform Team
