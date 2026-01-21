# Arquitetura da Plataforma MCP

## Visão Geral

A plataforma MCP TCloud implementa uma arquitetura de **diagnóstico orquestrado** onde múltiplos agents especialistas trabalham em paralelo para analisar problemas reportados por clientes.

## Diagrama de Arquitetura

```
┌─────────────────────────────────────────────────────────────────────────┐
│                              CLIENTES                                    │
├─────────────────────────────────────────────────────────────────────────┤
│  Sistema de Suporte  │  Claude Desktop  │  Aplicações Internas          │
└──────────┬───────────┴────────┬─────────┴───────────┬───────────────────┘
           │                    │                     │
           └────────────────────┼─────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                        MCP CONTEXT FORGE                                 │
│                         (Gateway Central)                                │
├─────────────────────────────────────────────────────────────────────────┤
│  • Federação de múltiplos MCP Servers                                   │
│  • Autenticação centralizada (OAuth 2.1)                                │
│  • Rate limiting e quotas                                               │
│  • Observabilidade (OpenTelemetry)                                      │
│  • Cache com Redis                                                      │
│  • Registro dinâmico de agents                                          │
└──────────┬──────────────────────────────────────────────────────────────┘
           │
           │ Registra e roteia para agents
           │
┌──────────┼──────────────────────────────────────────────────────────────┐
│          │              AGENTS ESPECIALISTAS                             │
├──────────┼──────────────────────────────────────────────────────────────┤
│          │                                                               │
│    ┌─────┴─────┐                                                        │
│    │           │                                                        │
│    ▼           ▼                                                        │
│ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐       │
│ │ Orques-  │ │ CPU/RAM  │ │ Database │ │ Network  │ │   App    │       │
│ │ trador   │ │  Agent   │ │  Agent   │ │  Agent   │ │  Agent   │       │
│ │          │ │          │ │          │ │          │ │          │       │
│ │ Triagem  │ │ Métricas │ │ Queries  │ │ Ping     │ │ ERP      │       │
│ │ Consoli- │ │ Picos    │ │ Locks    │ │ Firewall │ │ Tabelas  │       │
│ │ dação    │ │ Anomalias│ │ Deadlock │ │ Rotas    │ │ Processos│       │
│ └──────────┘ └──────────┘ └──────────┘ └──────────┘ └──────────┘       │
│      │            │            │            │            │              │
│      │            ▼            ▼            ▼            ▼              │
│      │       ┌─────────────────────────────────────────────┐           │
│      │       │           FONTES DE DADOS                    │           │
│      │       ├─────────────────────────────────────────────┤           │
│      │       │ TCloud Monitors API │ CloudWatch │ Prometheus│           │
│      │       │ TCloud API          │ RDS        │ Zabbix    │           │
│      │       │ S3 Metrics          │ Network    │ APM       │           │
│      │       └─────────────────────────────────────────────┘           │
│      │                                                                  │
│      └──────────────────────────────────────────────────────────────────┤
│                         Consolida micro-diagnósticos                    │
│                         em laudo final                                  │
└─────────────────────────────────────────────────────────────────────────┘
```

## Fluxo de Diagnóstico

```
1. GATILHO
   Cliente relata: "Sistema lento, não consigo acessar o ERP"
                            │
                            ▼
2. TRIAGEM (Agent Orquestrador)
   Analisa keywords e decide:
   • "lento" → CPU/RAM Agent ✓
   • "ERP" → App Agent ✓
   • "não acesso" → Network Agent ✓
                            │
                            ▼
3. EXECUÇÃO PARALELA
   ┌─────────────┬─────────────┬─────────────┐
   │  CPU/RAM    │    App      │   Network   │
   │  15 seg     │    20 seg   │    10 seg   │
   └─────────────┴─────────────┴─────────────┘
                            │
                            ▼
4. CONSOLIDAÇÃO
   Agent Orquestrador recebe micro-diagnósticos:
   • CPU: "Pico de 95% às 14:30" (warning)
   • App: "Tabela SC5 com lock" (critical)
   • Network: "Conectividade OK" (normal)
                            │
                            ▼
5. LAUDO FINAL
   {
     "severity": "critical",
     "root_cause": "Lock na tabela SC5 causando lentidão",
     "contributing_factors": ["Pico de CPU"],
     "recommendations": [...]
   }
```

## Componentes

### MCP Context Forge

O gateway central que:
- **Federa** múltiplos MCP Servers sob um único endpoint
- **Autentica** requisições via OAuth 2.1
- **Roteia** chamadas para os agents apropriados
- **Cacheia** respostas frequentes com Redis
- **Monitora** latência e erros via OpenTelemetry

**Deploy**: Kubernetes (este repositório)

### Agent Orquestrador

Agent especial responsável por:
- **Triagem**: Analisar a descrição do problema e decidir quais agents acionar
- **Coordenação**: Chamar agents em paralelo
- **Consolidação**: Unificar micro-diagnósticos em laudo final
- **Correlação**: Identificar relações entre findings de diferentes agents

**Deploy**: MCP Server (Lambda ou Docker)

### Agents Especialistas

Cada agent é especialista em um domínio:

| Agent | Domínio | Tools Principais |
|-------|---------|------------------|
| CPU/RAM | Computação | `analyze_cpu_ram`, `diagnose_vm_health` |
| Database | Banco de dados | `analyze_slow_queries`, `detect_locks` |
| Network | Conectividade | `ping_test`, `check_firewall` |
| Application | ERP/Apps | `check_erp_health`, `analyze_processes` |
| Storage | Disco/I/O | `analyze_disk_usage`, `check_iops` |

**Deploy**: MCP Server (Lambda, Docker, ou Kubernetes)

## Estrutura do Micro-diagnóstico

Todos os agents retornam um formato padronizado:

```json
{
  "agent": "cpu-ram",
  "timestamp": "2024-01-20T17:30:00Z",
  "topology_id": 123,
  "severity": "warning",
  "summary": "Picos de CPU detectados nos últimos 15 minutos",
  "findings": [
    {
      "type": "cpu_spike",
      "severity": "warning",
      "instance": "vm-app-01",
      "details": "CPU atingiu 95% às 17:25",
      "evidence": {
        "metric": "cpu_percent",
        "value": 95,
        "threshold": 80,
        "timestamp": "2024-01-20T17:25:00Z"
      }
    }
  ],
  "recommendations": [
    "Verificar processos consumindo CPU",
    "Considerar scaling horizontal"
  ],
  "metrics_snapshot": {
    "cpu_avg": 78,
    "cpu_max": 95,
    "ram_avg": 65
  }
}
```

## Segurança

### Autenticação

```
Cliente → OAuth 2.1 → Context Forge → Agent
                ↓
         Cognito + Fluig Identity
```

### Autorização

- Cada agent valida permissões do usuário para os recursos solicitados
- Context Forge pode aplicar políticas adicionais (rate limiting, quotas)

### Rede

- Agents em rede privada (VPC)
- Context Forge exposto via Ingress com TLS
- Comunicação agent ↔ Context Forge via mTLS (opcional)

## Observabilidade

### Métricas

- Latência por agent
- Taxa de erros
- Throughput de requisições
- Uso de recursos (CPU, memória)

### Logs

Formato estruturado JSON:
```json
{
  "timestamp": "2024-01-20T17:30:00Z",
  "level": "INFO",
  "service": "cpu-ram-agent",
  "event": "tool_call",
  "tool": "analyze_cpu_ram",
  "duration_ms": 1234,
  "user": "wagner.alexandre@totvs.com.br"
}
```

### Tracing

OpenTelemetry traces propagados:
```
Context Forge → Agent Orquestrador → [CPU Agent, DB Agent, Network Agent]
     └── trace_id: abc123 ──────────────────────────────────────────┘
```

## Escalabilidade

### Horizontal

- Context Forge: 3-20 replicas (auto-scaling)
- Agents em Lambda: escala automática
- Agents em K8s: HPA configurado

### Caching

- Redis para cache de respostas frequentes
- TTL configurável por tipo de dado
- Invalidação manual via API admin

## Disaster Recovery

### Backups

- PostgreSQL: backups diários, retenção 30 dias
- Redis: snapshots a cada 6 horas

### Failover

- Multi-AZ para PostgreSQL e Redis
- Agents em múltiplas AZs
- Context Forge com anti-affinity rules
