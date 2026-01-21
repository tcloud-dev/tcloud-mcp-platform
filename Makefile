.PHONY: help deploy-context-forge new-agent register-agent logs status

ENV ?= dev
NAMESPACE_DEV = mcp-dev
NAMESPACE_PROD = mcp
CONTEXT_FORGE_CHART = https://github.com/IBM/mcp-context-forge/releases/download/v0.1.0/mcp-stack-0.1.0.tgz

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'

# ==================== Context Forge ====================

deploy-context-forge: ## Deploy MCP Context Forge (ENV=dev|prod)
ifeq ($(ENV),prod)
	@echo "🚀 Deploying Context Forge to PRODUCTION..."
	helm upgrade --install mcp-stack $(CONTEXT_FORGE_CHART) \
		--namespace $(NAMESPACE_PROD) \
		--create-namespace \
		-f infrastructure/context-forge/values.yaml \
		-f infrastructure/context-forge/values-prod.yaml \
		--wait --timeout 30m
else
	@echo "🚀 Deploying Context Forge to DEV..."
	helm upgrade --install mcp-stack $(CONTEXT_FORGE_CHART) \
		--namespace $(NAMESPACE_DEV) \
		--create-namespace \
		-f infrastructure/context-forge/values.yaml \
		-f infrastructure/context-forge/values-dev.yaml \
		--wait --timeout 30m
endif

undeploy-context-forge: ## Remove MCP Context Forge (ENV=dev|prod)
ifeq ($(ENV),prod)
	helm uninstall mcp-stack --namespace $(NAMESPACE_PROD)
else
	helm uninstall mcp-stack --namespace $(NAMESPACE_DEV)
endif

status: ## Show Context Forge status (ENV=dev|prod)
ifeq ($(ENV),prod)
	kubectl get all -n $(NAMESPACE_PROD)
	@echo ""
	helm status mcp-stack -n $(NAMESPACE_PROD)
else
	kubectl get all -n $(NAMESPACE_DEV)
	@echo ""
	helm status mcp-stack -n $(NAMESPACE_DEV)
endif

logs: ## Tail Context Forge logs (ENV=dev|prod)
ifeq ($(ENV),prod)
	kubectl logs -f -l app=mcp-gateway -n $(NAMESPACE_PROD)
else
	kubectl logs -f -l app=mcp-gateway -n $(NAMESPACE_DEV)
endif

# ==================== Agent Management ====================

new-agent: ## Create new agent from template (NAME=my-agent)
ifndef NAME
	$(error NAME is required. Usage: make new-agent NAME=my-agent)
endif
	@echo "📦 Creating new agent: $(NAME)"
	@cp -r templates/mcp-agent-docker /tmp/$(NAME)
	@cd /tmp/$(NAME) && \
		find . -type f -exec sed -i '' 's/{{AGENT_NAME}}/$(NAME)/g' {} \;
	@echo "✅ Agent template created at /tmp/$(NAME)"
	@echo ""
	@echo "Next steps:"
	@echo "  1. Move to your preferred location"
	@echo "  2. Initialize git: cd /tmp/$(NAME) && git init"
	@echo "  3. Create GitHub repo: gh repo create tcloud-dev/$(NAME) --source=."
	@echo "  4. Implement your tools in src/tools.py"
	@echo "  5. Implement your prompts in src/prompts.py"

register-agent: ## Register agent in Context Forge (NAME=my-agent URL=https://...)
ifndef NAME
	$(error NAME is required. Usage: make register-agent NAME=my-agent URL=https://...)
endif
ifndef URL
	$(error URL is required. Usage: make register-agent NAME=my-agent URL=https://...)
endif
ifeq ($(ENV),prod)
	@echo "📝 Registering agent $(NAME) in PRODUCTION Context Forge..."
	curl -X POST https://mcp-gateway.tcloud.internal/admin/gateways \
		-H "Content-Type: application/json" \
		-d '{"name": "$(NAME)", "url": "$(URL)", "transport": "sse"}'
else
	@echo "📝 Registering agent $(NAME) in DEV Context Forge..."
	curl -X POST https://mcp-gateway.dev.tcloud.internal/admin/gateways \
		-H "Content-Type: application/json" \
		-d '{"name": "$(NAME)", "url": "$(URL)", "transport": "sse"}'
endif

list-agents: ## List registered agents (ENV=dev|prod)
ifeq ($(ENV),prod)
	curl -s https://mcp-gateway.tcloud.internal/admin/gateways | jq
else
	curl -s https://mcp-gateway.dev.tcloud.internal/admin/gateways | jq
endif

# ==================== Development ====================

validate: ## Validate Helm values
	helm lint infrastructure/context-forge/ || true
	@echo "✅ Validation complete"

template: ## Render Helm templates locally (ENV=dev|prod)
ifeq ($(ENV),prod)
	helm template mcp-stack $(CONTEXT_FORGE_CHART) \
		-f infrastructure/context-forge/values.yaml \
		-f infrastructure/context-forge/values-prod.yaml
else
	helm template mcp-stack $(CONTEXT_FORGE_CHART) \
		-f infrastructure/context-forge/values.yaml \
		-f infrastructure/context-forge/values-dev.yaml
endif
