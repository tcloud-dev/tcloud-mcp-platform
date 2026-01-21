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

```
┌─────────────────────────────────────────────────────────────────────┐
│  Clients (Support System, Applications)                              │
└──────────────────────────┬──────────────────────────────────────────┘
                           ▼
┌─────────────────────────────────────────────────────────────────────┐
│              🧠 Orchestrator Agent (Triage)                          │
└──────────────────────────┬──────────────────────────────────────────┘
                           ▼
┌─────────────────────────────────────────────────────────────────────┐
│                   MCP Context Forge (Gateway)                        │
│                   This repository manages deployment                 │
└────┬──────────┬──────────┬──────────┬──────────┬────────────────────┘
     ▼          ▼          ▼          ▼          ▼
┌─────────┐┌─────────┐┌─────────┐┌─────────┐┌─────────┐
│ CPU/RAM ││   DB    ││   App   ││ Network ││ Storage │
│  Agent  ││  Agent  ││  Agent  ││  Agent  ││  Agent  │
└─────────┘└─────────┘└─────────┘└─────────┘└─────────┘
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
| Dev | mcp-dev | https://mcp-gateway.dev.tcloud.internal |
| Prod | mcp | https://mcp-gateway.tcloud.internal |

## Related Repositories

- [tcloud-watch-mcp-server](https://github.com/tcloud-dev/tcloud-watch-mcp-server) - CPU/RAM Agent
- [MCP Context Forge](https://github.com/IBM/mcp-context-forge) - Gateway (upstream)
