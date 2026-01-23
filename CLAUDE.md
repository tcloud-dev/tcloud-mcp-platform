# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

TCloud MCP Platform is a centralized orchestration platform for MCP (Model Context Protocol) Agents. It manages the MCP Context Forge gateway deployment (IBM) and provides templates for teams to create new agents.

## Common Commands

```bash
# Deploy Context Forge gateway
make deploy-context-forge ENV=dev    # or ENV=prod

# Check deployment status
make status ENV=dev

# View gateway logs
make logs ENV=dev

# Port forward for local testing
make port-forward ENV=dev            # Access at http://localhost:9080

# Test endpoints
make test-health                     # Requires port-forward first
make test-mcp                        # Test MCP tools/list

# Create new agent from template
make new-agent NAME=my-agent

# Plugin management
make test-plugin                     # Run plugin unit tests
make build-plugin-configmap          # Build ConfigMap from plugin code
make deploy-plugin-configmap ENV=dev # Deploy plugin to cluster

# Render Helm templates locally (dry-run)
make template ENV=dev
```

## Architecture

```
Clients → Orchestrator Agent → MCP Context Forge (Gateway) → Specialist Agents
                                      │
                    ┌─────────────────┼─────────────────┐
                    ↓                 ↓                 ↓
              CPU/RAM Agent      DB Agent         App Agent
```

**Key Components:**
- **MCP Context Forge**: Central gateway that federates multiple MCP servers (IBM upstream chart)
- **Specialist Agents**: Domain-specific agents (CPU/RAM, Database, Network, etc.)
- **Authentication Plugin**: `plugins/tcloud_cognito_auth/` - Cognito JWT validation + TCloud API permissions (✅ Deployed)

**Docker Image (with plugin):** `ghcr.io/tcloud-dev/mcp-context-forge:with-auth`

## Project Structure

- `infrastructure/context-forge/` - Helm values for Context Forge deployment
  - `values.yaml` - Base configuration
  - `values-dev.yaml` - Dev environment overrides
  - `values-prod.yaml` - Prod environment overrides
- `plugins/tcloud_cognito_auth/` - Authentication plugin (Cognito + TCloud API)
- `templates/mcp-agent-docker/` - Template for creating new MCP agents
- `docs/` - Architecture, agent creation guide, authentication docs

## Environments

| Environment | Namespace | Gateway URL |
|-------------|-----------|-------------|
| Dev | mcp-dev | https://mcp-gateway.tbf8b9d.k8s.sp06.te.tks.sh |
| Prod | mcp | https://mcp-gateway.tcloud.internal (planned) |

## Important Configuration Notes

**Dev Ingress:**
- Do NOT set `ingressClassName` in values-dev.yaml (external controller picks up ingresses without class)
- TLS should be `false` - external ingress handles HTTPS automatically

**Common Issues:**
- Migration job stuck: `kubectl -n mcp-dev delete job mcp-stack-migration` then deploy with `--no-hooks`
- Redis 8.4 crash: Remove inline comments from redis configmap (e.g., `save 900 1 # comment` → separate lines)
- PVC multi-attach: Scale down old replicaset before new pods can attach

## Code Conventions

**MCP Agent Tool Response Format** (all diagnostic tools must use):
```python
{
    "agent": "agent-name",
    "timestamp": "ISO8601",
    "severity": "critical|warning|normal",
    "summary": "One-line summary",
    "findings": [{"type": "...", "severity": "...", "details": "...", "evidence": {}}],
    "recommendations": ["Action 1", "Action 2"]
}
```

**Git**: Use conventional commits (`feat:`, `fix:`, `docs:`, `chore:`)

## Serena MCP Integration

This project has Serena MCP configured. When Serena is active, memories are available in `.serena/memories/`:
- `project_overview` - Architecture and structure
- `suggested_commands` - Common kubectl and make commands
- `code_style_conventions` - Code style guidelines
