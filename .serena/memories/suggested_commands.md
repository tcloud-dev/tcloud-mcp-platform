# Suggested Commands

## Context Forge Deployment

```bash
# Deploy to dev
make deploy-context-forge ENV=dev

# Deploy to prod
make deploy-context-forge ENV=prod

# Check status
make status ENV=dev

# View logs
make logs ENV=dev

# Undeploy
make undeploy-context-forge ENV=dev
```

## Agent Management

```bash
# Create new agent from template
make new-agent NAME=my-agent

# Register agent in Context Forge
make register-agent NAME=my-agent URL=https://my-agent.example.com/mcp

# List registered agents
make list-agents ENV=dev
```

## Helm Operations

```bash
# Validate Helm values
make validate

# Render templates locally (dry-run)
make template ENV=dev
```

## Kubernetes

```bash
# Check pods
kubectl get pods -n mcp-dev

# Check services
kubectl get svc -n mcp-dev

# Check ingress
kubectl get ingress -n mcp-dev

# Describe gateway pod
kubectl describe pod -l app=mcp-gateway -n mcp-dev

# Port forward for local testing
kubectl port-forward svc/mcp-gateway 8000:8000 -n mcp-dev
```

## Testing

```bash
# Test gateway health
curl https://mcp-gateway.dev.tcloud.internal/health

# List tools via MCP
curl -X POST https://mcp-gateway.dev.tcloud.internal/mcp \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/list"}'

# MCP Inspector
npx @modelcontextprotocol/inspector https://mcp-gateway.dev.tcloud.internal/mcp
```
