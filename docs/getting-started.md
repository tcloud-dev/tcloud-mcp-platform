# Getting Started

Guia para começar a usar a plataforma MCP TCloud.

## Pré-requisitos

- Acesso ao cluster Kubernetes TCloud
- `kubectl` configurado
- `helm` v3 instalado
- Docker (para criar agents)

## 1. Deploy do MCP Context Forge

O Context Forge é o gateway central que orquestra todos os agents MCP.

### Verificar pré-requisitos do cluster

```bash
# Verificar StorageClass
kubectl get storageclasses

# Verificar IngressClass
kubectl get ingressclass
```

### Deploy em Dev

```bash
make deploy-context-forge ENV=dev
```

### Verificar status

```bash
make status ENV=dev
```

### Acessar o gateway

Após o deploy, o gateway estará disponível em:
- **Dev**: https://mcp-gateway.dev.tcloud.internal
- **Prod**: https://mcp-gateway.tcloud.internal

## 2. Registrar um Agent existente

Se você já tem um Agent MCP rodando (ex: AWS Lambda), registre-o no Context Forge:

```bash
make register-agent NAME=cpu-ram URL=https://xxx.execute-api.sa-east-1.amazonaws.com/dev/mcp
```

### Verificar agents registrados

```bash
make list-agents ENV=dev
```

## 3. Criar um novo Agent

Veja [creating-agents.md](creating-agents.md) para o guia completo.

```bash
# Criar a partir do template
make new-agent NAME=meu-agent
```

## 4. Testar a integração

### Via curl

```bash
# Listar tools disponíveis
curl -X POST https://mcp-gateway.dev.tcloud.internal/mcp \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/list"}'
```

### Via MCP Inspector

```bash
npx @modelcontextprotocol/inspector https://mcp-gateway.dev.tcloud.internal/mcp
```

## Troubleshooting

### Gateway não inicia

```bash
# Ver logs
make logs ENV=dev

# Ver eventos do pod
kubectl describe pod -l app=mcp-gateway -n mcp-dev
```

### Agent não conecta

1. Verificar se o agent está acessível da rede do cluster
2. Verificar se o transport (SSE/HTTP) está correto
3. Ver logs do gateway para erros de conexão

## Próximos passos

- [Criar um Agent personalizado](creating-agents.md)
- [Arquitetura da plataforma](architecture.md)
