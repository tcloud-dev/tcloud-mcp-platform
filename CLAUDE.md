# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

TCloud MCP Platform is an infrastructure-as-code repository for orchestrating MCP (Model Context Protocol) agents in the TCloud ecosystem. It does **not** contain application code — it manages the deployment of **MCP Context Forge** (an IBM open-source gateway) on Kubernetes via Helm, and provides templates for creating new MCP agent services.

The platform implements a **federated diagnostics architecture**: multiple specialist agents (CPU/RAM, Database, Network, Application, Storage) are registered in Context Forge, which exposes them through a single MCP endpoint. An orchestrator agent performs triage, parallel execution, and consolidation of micro-diagnostics into a final report.

## Common Commands

All commands use `make` with an optional `ENV=dev|prod` parameter (defaults to `dev`):

```bash
# Deploy Context Forge gateway to Kubernetes
make deploy-context-forge ENV=dev

# Remove Context Forge
make undeploy-context-forge ENV=dev

# Check pod/service/pvc status
make status ENV=dev

# Tail gateway logs
make logs ENV=dev

# Port forward gateway to localhost:9080
make port-forward ENV=dev

# Test health endpoint (requires port-forward running)
make test-health

# Test MCP tools/list endpoint (requires port-forward running)
make test-mcp

# Render Helm templates locally without deploying
make template ENV=dev

# Re-clone the IBM chart to get updates
make update-chart
```

### Agent Management

```bash
# Scaffold a new agent from the Docker template
make new-agent NAME=my-agent

# Show registration command for an agent
make register-agent NAME=my-agent URL=https://my-agent.example.com/mcp

# List registered agents (requires port-forward running)
make list-agents
```

## Architecture & Key Paths

- `infrastructure/context-forge/` — Helm values for Context Forge deployment
  - `values.yaml` — Base configuration (shared across environments)
  - `values-dev.yaml` — Dev overrides (cluster `tbf8b9d`, namespace `mcp-dev`, single replica, NodePort)
  - `values-prod.yaml` — Prod overrides (3-20 replicas, TLS, external secrets)
- `templates/mcp-agent-docker/` — Cookiecutter-style template for new agents (placeholder `{{AGENT_NAME}}` replaced by `make new-agent`)
- `docs/` — Architecture diagrams, getting-started guide, agent creation guide

The Helm chart itself is **not** in this repo — it's cloned from `github.com/IBM/mcp-context-forge` into `/tmp/mcp-context-forge` at deploy time.

## Agent Template Structure

The Docker template at `templates/mcp-agent-docker/` produces a Python MCP server using the `mcp` SDK with Starlette/Uvicorn and SSE transport:

- `src/server.py` — MCP server bootstrap (routes: `/health`, `/mcp`, `/mcp/messages`). Not meant to be modified.
- `src/tools.py` — Tool definitions via `register(server)` pattern. Each tool returns `list[TextContent]`.
- `src/prompts.py` — Prompt template definitions via `register(server)` pattern.
- `src/config.py` — Environment-based configuration (host, port, log level).

## Micro-diagnostic Return Format

All agents must return a standardized JSON structure for orchestrator consolidation:

```json
{
  "agent": "<agent-name>",
  "timestamp": "ISO8601",
  "severity": "critical|warning|normal",
  "summary": "One-line summary",
  "findings": [{ "type": "...", "severity": "...", "details": "...", "evidence": {} }],
  "recommendations": ["..."]
}
```

## Environment Details

| Environment | Namespace | Gateway URL | Notes |
|-------------|-----------|-------------|-------|
| Dev | `mcp-dev` | `https://mcp-gateway.tbf8b9d.k8s.sp06.te.tks.sh` | Single replica, debug logging |
| Prod | `mcp` | `https://mcp-gateway.tcloud.internal` | Planned, 3-20 replicas, TLS |

## Infrastructure Stack

Context Forge deploys: the gateway app (gunicorn), PostgreSQL (agent registry, config), and Redis (response cache). Secrets (admin password, JWT key, Postgres password) are auto-generated at deploy time and printed to stdout.

## Prerequisites

- `kubectl` configured for the target cluster
- `helm` v3
- Docker (for building agents)
