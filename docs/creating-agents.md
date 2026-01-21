# Criando um Agent MCP

Guia completo para criar um novo Agent MCP para a plataforma TCloud.

## Visão Geral

Um Agent MCP é um serviço que expõe **tools** (funções) e **prompts** (templates) via o protocolo MCP. O Context Forge orquestra múltiplos agents, permitindo que clientes (como Claude) acessem todas as funcionalidades através de um único endpoint.

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────┐
│  Claude/Client  │────▶│  Context Forge   │────▶│  Seu Agent  │
└─────────────────┘     └──────────────────┘     └─────────────┘
```

## Opções de Deploy

| Opção | Complexidade | Melhor para |
|-------|--------------|-------------|
| **Docker** (recomendado) | Baixa | Maioria dos casos |
| **AWS Lambda** | Média | Equipes com experiência AWS |
| **Kubernetes** | Alta | Agents com requisitos especiais |

## Criando via Template Docker (Recomendado)

### 1. Gerar o projeto

```bash
make new-agent NAME=meu-agent
cd /tmp/meu-agent
```

### 2. Estrutura gerada

```
meu-agent/
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── src/
│   ├── __init__.py
│   ├── server.py       # Servidor MCP (não mexer)
│   ├── tools.py        # 👈 Implemente suas tools aqui
│   ├── prompts.py      # 👈 Implemente seus prompts aqui
│   └── config.py       # Configurações
├── tests/
│   └── test_tools.py
└── README.md
```

### 3. Implementar Tools

Edite `src/tools.py`:

```python
from mcp.server import Server
from mcp.types import Tool, TextContent

server = Server("meu-agent")

@server.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(
            name="minha_tool",
            description="Descrição do que a tool faz",
            inputSchema={
                "type": "object",
                "properties": {
                    "param1": {
                        "type": "string",
                        "description": "Descrição do parâmetro"
                    }
                },
                "required": ["param1"]
            }
        )
    ]

@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    if name == "minha_tool":
        param1 = arguments.get("param1")

        # Sua lógica aqui
        resultado = f"Processado: {param1}"

        return [TextContent(type="text", text=resultado)]

    raise ValueError(f"Tool desconhecida: {name}")
```

### 4. Implementar Prompts (Opcional)

Edite `src/prompts.py`:

```python
from mcp.server import Server
from mcp.types import Prompt, PromptMessage, TextContent

server = Server("meu-agent")

@server.list_prompts()
async def list_prompts() -> list[Prompt]:
    return [
        Prompt(
            name="analise_diagnostica",
            description="Template para análise diagnóstica",
            arguments=[
                {
                    "name": "contexto",
                    "description": "Contexto do problema",
                    "required": True
                }
            ]
        )
    ]

@server.get_prompt()
async def get_prompt(name: str, arguments: dict) -> list[PromptMessage]:
    if name == "analise_diagnostica":
        contexto = arguments.get("contexto", "")

        return [
            PromptMessage(
                role="user",
                content=TextContent(
                    type="text",
                    text=f"""Analise o seguinte contexto e forneça um diagnóstico:

{contexto}

Forneça:
1. Problemas identificados
2. Severidade (critical/warning/normal)
3. Recomendações
"""
                )
            )
        ]

    raise ValueError(f"Prompt desconhecido: {name}")
```

### 5. Testar localmente

```bash
# Subir com docker-compose
docker-compose up

# Testar via MCP Inspector
npx @modelcontextprotocol/inspector http://localhost:8000/mcp
```

### 6. Build e Push

```bash
# Build
docker build -t ghcr.io/tcloud-dev/meu-agent:latest .

# Push (precisa autenticar no ghcr.io)
docker push ghcr.io/tcloud-dev/meu-agent:latest
```

### 7. Deploy e Registro

```bash
# Se rodando em K8s, criar deployment
kubectl apply -f k8s/

# Registrar no Context Forge
make register-agent NAME=meu-agent URL=https://meu-agent.tcloud.internal/mcp
```

## Boas Práticas

### Nomenclatura de Tools

- Use nomes descritivos: `analyze_cpu_usage` ao invés de `analyze`
- Prefixe com o domínio: `db_query_slow_logs`, `network_ping_test`

### Estrutura do Retorno

Padronize o formato de retorno para facilitar a consolidação pelo orquestrador:

```python
{
    "agent": "meu-agent",
    "timestamp": "2024-01-20T17:30:00Z",
    "severity": "warning",  # critical | warning | normal
    "summary": "Resumo em uma linha",
    "findings": [
        {
            "type": "tipo_do_problema",
            "severity": "warning",
            "details": "Detalhes do problema",
            "evidence": "Dados que comprovam"
        }
    ],
    "recommendations": [
        "Ação recomendada 1",
        "Ação recomendada 2"
    ],
    "raw_data": { }  # Dados brutos opcionais
}
```

### Tratamento de Erros

```python
@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    try:
        # sua lógica
        pass
    except MyAPIError as e:
        return [TextContent(
            type="text",
            text=json.dumps({
                "agent": "meu-agent",
                "severity": "error",
                "summary": f"Erro ao executar {name}",
                "error": str(e)
            })
        )]
```

### Logging

Use logging estruturado para facilitar debugging:

```python
import logging
import json

logger = logging.getLogger(__name__)

@server.call_tool()
async def call_tool(name: str, arguments: dict):
    logger.info(json.dumps({
        "event": "tool_call",
        "tool": name,
        "arguments": arguments
    }))
```

## Exemplos

### Agent CPU/RAM

Veja o [tcloud-watch-mcp-server](https://github.com/tcloud-dev/tcloud-watch-mcp-server) como referência de um agent completo com:
- Tools para buscar métricas
- Tools para análise diagnóstica
- Prompts especializados
- Deploy via AWS Lambda

## Suporte

- Abra uma issue em [tcloud-mcp-platform](https://github.com/tcloud-dev/tcloud-mcp-platform/issues)
- Canal Slack: #tcloud-mcp-platform
