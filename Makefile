.PHONY: help deploy-context-forge clone-chart new-agent register-agent logs status

ENV ?= dev
NAMESPACE_DEV = mcp-dev
NAMESPACE_PROD = mcp
CHART_DIR = /tmp/mcp-context-forge
CHART_PATH = $(CHART_DIR)/charts/mcp-stack

# Secrets - override via environment or make args
POSTGRES_PASSWORD ?= $(shell openssl rand -base64 16 | tr -d '=+/')
JWT_SECRET ?= $(shell openssl rand -hex 32)
ADMIN_PASSWORD ?= $(shell openssl rand -base64 12 | tr -d '=+/')

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'

# ==================== Context Forge ====================

clone-chart: ## Clone MCP Context Forge chart from IBM
	@if [ ! -d "$(CHART_DIR)" ]; then \
		echo "📦 Cloning MCP Context Forge chart..."; \
		git clone --depth 1 https://github.com/IBM/mcp-context-forge.git $(CHART_DIR); \
	else \
		echo "✅ Chart already exists at $(CHART_DIR)"; \
	fi

deploy-context-forge: clone-chart ## Deploy MCP Context Forge (ENV=dev|prod)
ifeq ($(ENV),prod)
	@echo "🚀 Deploying Context Forge to PRODUCTION..."
	helm upgrade --install mcp-stack $(CHART_PATH) \
		--namespace $(NAMESPACE_PROD) \
		--create-namespace \
		-f infrastructure/context-forge/values.yaml \
		-f infrastructure/context-forge/values-prod.yaml \
		--set mcpContextForge.secret.BASIC_AUTH_PASSWORD="$(ADMIN_PASSWORD)" \
		--set mcpContextForge.secret.JWT_SECRET_KEY="$(JWT_SECRET)" \
		--set postgres.credentials.password="$(POSTGRES_PASSWORD)" \
		--wait --timeout 10m
	@echo ""
	@echo "🔐 Secrets generated (save these!):"
	@echo "   ADMIN_PASSWORD: $(ADMIN_PASSWORD)"
	@echo "   POSTGRES_PASSWORD: $(POSTGRES_PASSWORD)"
else
	@echo "🚀 Deploying Context Forge to DEV..."
	helm upgrade --install mcp-stack $(CHART_PATH) \
		--namespace $(NAMESPACE_DEV) \
		--create-namespace \
		-f infrastructure/context-forge/values.yaml \
		-f infrastructure/context-forge/values-dev.yaml \
		--set mcpContextForge.secret.BASIC_AUTH_PASSWORD="$(ADMIN_PASSWORD)" \
		--set mcpContextForge.secret.JWT_SECRET_KEY="$(JWT_SECRET)" \
		--set postgres.credentials.password="$(POSTGRES_PASSWORD)" \
		--wait --timeout 10m
	@echo ""
	@echo "🔐 Secrets generated (save these!):"
	@echo "   ADMIN_PASSWORD: $(ADMIN_PASSWORD)"
	@echo "   POSTGRES_PASSWORD: $(POSTGRES_PASSWORD)"
	@echo ""
	@echo "🔧 Patching NodePort to 30080..."
	kubectl patch svc mcp-stack-mcpgateway -n $(NAMESPACE_DEV) --type='json' \
		-p='[{"op": "replace", "path": "/spec/ports/0/nodePort", "value": 30080}]' || true
	@echo "🌐 Patching Ingress to use public controller (remove ingressClassName)..."
	kubectl patch ingress mcp-stack-ingress -n $(NAMESPACE_DEV) --type=json \
		-p='[{"op": "remove", "path": "/spec/ingressClassName"}]' || true
	@echo ""
	@echo "✅ MCP Context Forge deployed!"
	@echo "   URL: https://mcp-gateway.tbf8b9d.k8s.sp06.te.tks.sh"
	@echo "   Admin: admin@example.com / $(ADMIN_PASSWORD)"
endif

undeploy-context-forge: ## Remove MCP Context Forge (ENV=dev|prod)
ifeq ($(ENV),prod)
	helm uninstall mcp-stack --namespace $(NAMESPACE_PROD)
else
	helm uninstall mcp-stack --namespace $(NAMESPACE_DEV)
endif

status: ## Show Context Forge status (ENV=dev|prod)
ifeq ($(ENV),prod)
	@echo "📊 Status: PRODUCTION"
	@echo ""
	kubectl get pods -n $(NAMESPACE_PROD)
	@echo ""
	kubectl get svc -n $(NAMESPACE_PROD)
	@echo ""
	kubectl get pvc -n $(NAMESPACE_PROD)
else
	@echo "📊 Status: DEV"
	@echo ""
	kubectl get pods -n $(NAMESPACE_DEV)
	@echo ""
	kubectl get svc -n $(NAMESPACE_DEV)
	@echo ""
	kubectl get pvc -n $(NAMESPACE_DEV)
endif

logs: ## Tail Context Forge logs (ENV=dev|prod)
ifeq ($(ENV),prod)
	kubectl logs -f -l app.kubernetes.io/name=mcp-context-forge -n $(NAMESPACE_PROD) --all-containers
else
	kubectl logs -f -l app.kubernetes.io/name=mcp-context-forge -n $(NAMESPACE_DEV) --all-containers
endif

port-forward: ## Port forward to access locally (ENV=dev|prod)
ifeq ($(ENV),prod)
	@echo "🔌 Port forwarding to PROD (http://localhost:9080)..."
	kubectl port-forward svc/mcp-stack-mcpgateway 9080:80 -n $(NAMESPACE_PROD)
else
	@echo "🔌 Port forwarding to DEV (http://localhost:9080)..."
	kubectl port-forward svc/mcp-stack-mcpgateway 9080:80 -n $(NAMESPACE_DEV)
endif

test-health: ## Test health endpoint via port-forward (run port-forward first)
	@echo "🏥 Testing health endpoint..."
	curl -s http://localhost:9080/health | jq

test-mcp: ## Test MCP tools/list via port-forward (run port-forward first)
	@echo "🔧 Testing MCP tools/list..."
	curl -s -X POST http://localhost:9080/mcp \
		-H "Content-Type: application/json" \
		-d '{"jsonrpc":"2.0","id":1,"method":"tools/list"}' | jq

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
	@echo "📝 Registering agent $(NAME)..."
	@echo "Run 'make port-forward' first, then:"
	@echo "curl -X POST http://localhost:8080/admin/gateways \\"
	@echo "  -H 'Content-Type: application/json' \\"
	@echo "  -u admin:<ADMIN_PASSWORD> \\"
	@echo "  -d '{\"name\": \"$(NAME)\", \"url\": \"$(URL)\", \"transport\": \"sse\"}'"

list-agents: ## List registered agents (run port-forward first)
	@echo "📋 Listing registered agents..."
	curl -s http://localhost:8080/admin/gateways | jq

# ==================== Development ====================

template: clone-chart ## Render Helm templates locally (ENV=dev|prod)
ifeq ($(ENV),prod)
	helm template mcp-stack $(CHART_PATH) \
		-f infrastructure/context-forge/values.yaml \
		-f infrastructure/context-forge/values-prod.yaml \
		--set mcpContextForge.secret.BASIC_AUTH_PASSWORD="placeholder" \
		--set mcpContextForge.secret.JWT_SECRET_KEY="placeholder" \
		--set postgres.credentials.password="placeholder"
else
	helm template mcp-stack $(CHART_PATH) \
		-f infrastructure/context-forge/values.yaml \
		-f infrastructure/context-forge/values-dev.yaml \
		--set mcpContextForge.secret.BASIC_AUTH_PASSWORD="placeholder" \
		--set mcpContextForge.secret.JWT_SECRET_KEY="placeholder" \
		--set postgres.credentials.password="placeholder"
endif

update-chart: ## Update MCP Context Forge chart (re-clone)
	@echo "🔄 Updating chart..."
	rm -rf $(CHART_DIR)
	git clone --depth 1 https://github.com/IBM/mcp-context-forge.git $(CHART_DIR)
	@echo "✅ Chart updated"
