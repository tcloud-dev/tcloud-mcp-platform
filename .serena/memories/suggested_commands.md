# Suggested Commands

## Docker Image (with Auth Plugin)

```bash
# Build image for linux/amd64 (required for K8s cluster)
docker build --platform linux/amd64 -t ghcr.io/tcloud-dev/mcp-context-forge:with-auth -f infrastructure/context-forge/Dockerfile .

# Authenticate with GHCR
gh auth refresh -h github.com -s write:packages
echo $(gh auth token) | docker login ghcr.io -u USERNAME --password-stdin

# Push image
docker push ghcr.io/tcloud-dev/mcp-context-forge:with-auth
```

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

# Port forward for local access
make port-forward ENV=dev

# Undeploy
make undeploy-context-forge ENV=dev
```

## Agent Management

```bash
# Create new agent from template
make new-agent NAME=my-agent

# Register agent in Context Forge (via Admin UI or API)
# Admin UI: https://mcp-gateway.tbf8b9d.k8s.sp06.te.tks.sh/admin/login

# List registered agents
make list-agents
```

## Helm Operations

```bash
# Render templates locally (dry-run)
make template ENV=dev

# Update chart from upstream
make update-chart
```

## Kubernetes

```bash
# Check pods
kubectl get pods -n mcp-dev

# Check services
kubectl get svc -n mcp-dev

# Check ingress
kubectl get ingress -n mcp-dev

# Check PVCs
kubectl get pvc -n mcp-dev

# Gateway logs
kubectl logs -l app=mcp-stack-mcpgateway -n mcp-dev

# Get admin password
kubectl -n mcp-dev get secret mcp-stack-gateway-secret -o jsonpath="{.data.BASIC_AUTH_PASSWORD}" | base64 -d
```

## Testing

```bash
# Test gateway health (via Ingress)
curl https://mcp-gateway.tbf8b9d.k8s.sp06.te.tks.sh/health

# Test health (via port-forward)
make port-forward ENV=dev  # then in another terminal:
curl http://localhost:9080/health

# List tools via MCP
curl -X POST https://mcp-gateway.tbf8b9d.k8s.sp06.te.tks.sh/mcp \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/list"}'
```

## Troubleshooting

```bash
# Fix stuck migration job
kubectl -n mcp-dev delete job mcp-stack-migration
helm upgrade ... --no-hooks

# Fix Redis config (Redis 8.4 inline comment issue)
# Edit configmap to remove inline comments from save lines
kubectl -n mcp-dev edit cm mcp-stack-redis-config
kubectl -n mcp-dev delete pods -l app=mcp-stack-redis

# Fix PVC multi-attach (when new pods can't start)
kubectl -n mcp-dev scale rs OLD_REPLICASET --replicas=0
# Wait for old pods to terminate, then new ones will attach

# Fix ingress not getting address
kubectl -n mcp-dev patch ingress mcp-stack-ingress --type=json -p='[{"op": "remove", "path": "/spec/ingressClassName"}]'

# Check plugin initialization
kubectl -n mcp-dev logs -l app=mcp-context-forge | grep -i "plugin\|cognito\|jwks"

# Rollback helm release
helm rollback mcp-stack -n mcp-dev
helm rollback mcp-stack REVISION -n mcp-dev
```

## URLs (Dev Environment)

- **Gateway**: https://mcp-gateway.tbf8b9d.k8s.sp06.te.tks.sh
- **Admin UI**: https://mcp-gateway.tbf8b9d.k8s.sp06.te.tks.sh/admin/login
- **Health**: https://mcp-gateway.tbf8b9d.k8s.sp06.te.tks.sh/health
- **MCP Endpoint**: https://mcp-gateway.tbf8b9d.k8s.sp06.te.tks.sh/mcp
