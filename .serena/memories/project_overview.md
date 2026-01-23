# TCloud MCP Platform - Project Overview

## Purpose
Centralized platform for orchestrating MCP (Model Context Protocol) Agents in the TCloud ecosystem. Manages the MCP Context Forge gateway deployment and provides templates for teams to create new agents.

## Tech Stack
- **Infrastructure**: Kubernetes, Helm
- **Gateway**: MCP Context Forge (IBM)
- **Agent Template**: Python 3.12, Docker
- **Database**: PostgreSQL (for Context Forge)
- **Cache**: Redis (for federation/caching)

## Architecture

```mermaid
flowchart TB
    subgraph Clients
        C1[Support System]
        C2[Applications]
    end

    subgraph Orchestration
        OA[🧠 Orchestrator Agent<br/>Triage]
    end

    subgraph Gateway
        MCF[MCP Context Forge<br/>This repo manages deployment]
    end

    subgraph Agents
        A1[CPU/RAM Agent]
        A2[DB Agent]
        A3[App Agent]
        A4[Network Agent]
        A5[Storage Agent]
    end

    C1 --> OA
    C2 --> OA
    OA --> MCF
    MCF --> A1
    MCF --> A2
    MCF --> A3
    MCF --> A4
    MCF --> A5
```

## Project Structure

```
tcloud-mcp-platform/
├── infrastructure/           # Context Forge deployment
│   └── context-forge/
│       ├── values.yaml       # Base Helm config
│       ├── values-dev.yaml   # Dev overrides
│       └── values-prod.yaml  # Prod overrides
├── templates/                # Agent templates for teams
│   └── mcp-agent-docker/     # Docker-based template
├── docs/                     # Documentation
│   ├── architecture.md
│   ├── creating-agents.md
│   └── getting-started.md
├── scripts/                  # Automation scripts
├── Makefile                  # Common commands
└── README.md
```

## Environments

| Environment | Namespace | Gateway URL |
|-------------|-----------|-------------|
| Dev | mcp-dev | https://mcp-gateway.tbf8b9d.k8s.sp06.te.tks.sh |
| Prod | mcp | https://mcp-gateway.tcloud.internal (planned) |

### Dev Environment Details (Cluster tbf8b9d)
- **Admin UI**: https://mcp-gateway.tbf8b9d.k8s.sp06.te.tks.sh/admin/login
- **Health**: https://mcp-gateway.tbf8b9d.k8s.sp06.te.tks.sh/health
- **Ingress**: Public controller (.223), no ingressClassName
- **Credentials**: 
  - Email: admin@example.com
  - Password: `kubectl -n mcp-dev get secret mcp-stack-gateway-secret -o jsonpath="{.data.BASIC_AUTH_PASSWORD}" | base64 -d`

## Authentication Plugin

| Plugin | Purpose | Status |
|--------|---------|--------|
| tcloud_cognito_auth | JWT validation via Cognito + TCloud API permissions | ✅ Implemented |

**Location:** `plugins/tcloud_cognito_auth/`

**Headers Propagated:**
- `X-User-Email` - User email
- `X-User-Customers` - JSON array of cloud_ids

## Registered Agents

| Agent | URL | Status |
|-------|-----|--------|
| tcloud-watch-mcp-server | https://api.tcloud-watch-mcp.example.com/mcp | ✅ Registrado |

## Related Repositories

- [tcloud-watch-mcp-server](https://github.com/tcloud-dev/tcloud-watch-mcp-server) - CPU/RAM Agent
- [MCP Context Forge](https://github.com/IBM/mcp-context-forge) - Gateway (upstream)
