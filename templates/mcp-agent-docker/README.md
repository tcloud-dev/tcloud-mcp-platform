# {{AGENT_NAME}} MCP Agent

Agent MCP especializado para [descreva o propósito do seu agent].

## Quick Start

### Desenvolvimento local

```bash
# Subir com docker-compose
docker-compose up

# Testar via MCP Inspector
npx @modelcontextprotocol/inspector http://localhost:8000/mcp
```

### Build e Deploy

```bash
# Build da imagem
docker build -t ghcr.io/tcloud-dev/{{AGENT_NAME}}:latest .

# Push para registry
docker push ghcr.io/tcloud-dev/{{AGENT_NAME}}:latest

# Registrar no Context Forge
curl -X POST https://mcp-gateway.dev.tcloud.internal/admin/gateways \
  -H "Content-Type: application/json" \
  -d '{"name": "{{AGENT_NAME}}", "url": "https://{{AGENT_NAME}}.tcloud.internal/mcp", "transport": "sse"}'
```

## Estrutura

```
{{AGENT_NAME}}/
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── src/
│   ├── __init__.py
│   ├── server.py      # Servidor MCP
│   ├── tools.py       # 👈 Implemente suas tools aqui
│   ├── prompts.py     # 👈 Implemente seus prompts aqui
│   └── config.py      # Configurações
└── README.md
```

## Tools Disponíveis

| Tool | Descrição |
|------|-----------|
| `example_tool` | Tool de exemplo - substitua pela sua |
| `diagnose` | Executa análise diagnóstica |

## Prompts Disponíveis

| Prompt | Descrição |
|--------|-----------|
| `diagnostic_analysis` | Template para análise diagnóstica |
| `health_report` | Template para relatório de saúde |

## Configuração

Variáveis de ambiente:

| Variável | Descrição | Default |
|----------|-----------|---------|
| `HOST` | Host do servidor | `0.0.0.0` |
| `PORT` | Porta do servidor | `8000` |
| `LOG_LEVEL` | Nível de log | `INFO` |

## Desenvolvimento

### Adicionar uma nova Tool

1. Edite `src/tools.py`
2. Adicione a definição em `list_tools()`
3. Implemente o handler em `call_tool()`

### Adicionar um novo Prompt

1. Edite `src/prompts.py`
2. Adicione a definição em `list_prompts()`
3. Implemente o template em `get_prompt()`

## Formato de Resposta Diagnóstica

Todas as tools de diagnóstico devem retornar este formato:

```json
{
  "agent": "{{AGENT_NAME}}",
  "timestamp": "2024-01-20T17:30:00Z",
  "severity": "warning",
  "summary": "Resumo do diagnóstico",
  "findings": [
    {
      "type": "tipo_do_problema",
      "severity": "warning",
      "details": "Detalhes",
      "evidence": {}
    }
  ],
  "recommendations": ["Ação 1", "Ação 2"],
  "raw_data": {}
}
```

## Licença

Proprietary - TOTVS
