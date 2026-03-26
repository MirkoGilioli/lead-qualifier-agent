
# ==============================================================================
# Installation & Setup
# ==============================================================================

# Install dependencies using uv package manager
install:
	@command -v uv >/dev/null 2>&1 || { echo "uv is not installed. Installing uv..."; curl -LsSf https://astral.sh/uv/0.8.13/install.sh | sh; source $HOME/.local/bin/env; }
	uv sync

# ==============================================================================
# Playground Targets
# ==============================================================================

# Launch local dev playground
playground:
	@echo "==============================================================================="
	@echo "| 🚀 Starting your agent playground...                                        |"
	@echo "|                                                                             |"
	@echo "| 💡 Try asking: What's the weather in San Francisco?                         |"
	@echo "|                                                                             |"
	@echo "| 🔍 IMPORTANT: Select the 'app' folder to interact with your agent.          |"
	@echo "==============================================================================="
	uv run adk web . --port 8501 --reload_agents

# ==============================================================================
# Testing & Code Quality
# ==============================================================================

# Run unit and integration tests
test:
	uv sync --dev
	uv run pytest tests/unit && uv run pytest tests/integration

# ==============================================================================
# Agent Evaluation
# ==============================================================================

# Run agent evaluation using ADK eval
# Usage: make eval [EVALSET=tests/eval/evalsets/basic.evalset.json] [EVAL_CONFIG=tests/eval/eval_config.json]
eval:
	@echo "==============================================================================="
	@echo "| Running Agent Evaluation                                                    |"
	@echo "==============================================================================="
	uv sync --dev --extra eval
	uv run adk eval ./app $${EVALSET:-tests/eval/evalsets/basic.evalset.json} \
		$(if $(EVAL_CONFIG),--config_file_path=$(EVAL_CONFIG),$(if $(wildcard tests/eval/eval_config.json),--config_file_path=tests/eval/eval_config.json,))

# Run evaluation with all evalsets
eval-all:
	@echo "==============================================================================="
	@echo "| Running All Evalsets                                                        |"
	@echo "==============================================================================="
	@for evalset in tests/eval/evalsets/*.evalset.json; do \
		echo ""; \
		echo "▶ Running: $$evalset"; \
		$(MAKE) eval EVALSET=$$evalset || exit 1; \
	done
	@echo ""
	@echo "✅ All evalsets completed"

# Run code quality checks (codespell, ruff, ty)
lint:
	uv sync --dev --extra lint
	uv run codespell
	uv run ruff check . --diff
	uv run ruff format . --check --diff
	uv run ty check .

# ==============================================================================
# Infrastructure (Terraform)
# ==============================================================================

# Define environment (default: dev)
ENV ?= dev
TF_DIR = deployment/terraform
TF_VARS = vars/$(ENV).tfvars
PROJECT_ID ?= $(shell gcloud config get-value project)
TF_BUCKET ?= $(PROJECT_ID)-tfstate

# Initialize Terraform for a specific environment
tf-init:
	@echo "Initializing Terraform for environment: $(ENV)"
	@cd $(TF_DIR) && terraform init \
		-backend-config="bucket=$(TF_BUCKET)" \
		-backend-config="prefix=terraform/state/$(ENV)" \
		-reconfigure

# Plan Terraform changes
tf-plan:
	@cd $(TF_DIR) && terraform plan -var-file=$(TF_VARS) -var="project_id=$(PROJECT_ID)"

# Apply Terraform changes
tf-apply:
	@cd $(TF_DIR) && terraform apply -var-file=$(TF_VARS) -var="project_id=$(PROJECT_ID)" -auto-approve

# Destroy Terraform infrastructure
tf-destroy:
	@cd $(TF_DIR) && terraform destroy -var-file=$(TF_VARS) -var="project_id=$(PROJECT_ID)" -auto-approve

# --- Commands from Agent Starter Pack ---

backend: deploy

deploy:
	@echo "Deploying to environment: $(ENV)"
	$(eval PROJECT_NAME := $(shell grep 'project_name' $(TF_DIR)/$(TF_VARS) | cut -d'"' -f2))
	$(eval REGION := $(shell grep 'region' $(TF_DIR)/$(TF_VARS) | cut -d'"' -f2))
	gcloud beta run deploy $(PROJECT_NAME)-$(ENV) \
		--source . \
		--memory "4Gi" \
		--project $(PROJECT_ID) \
		--region "$(REGION)" \
		--no-allow-unauthenticated \
		--no-cpu-throttling \
		--labels "created-by=adk" \
		--service-account "$(PROJECT_NAME)-app-$(ENV)@$(PROJECT_ID).iam.gserviceaccount.com" \
		--max-instances 10 \
		--min-instances 1 \
		--session-affinity \
		--update-build-env-vars "AGENT_VERSION=$(shell awk -F'"' '/^version = / {print $$2}' pyproject.toml || echo '0.0.0')" \
		--update-env-vars \
		"FIRESTORE_DATABASE_ID=lead-qualifier-db-$(ENV),LOGS_BUCKET_NAME=$(PROJECT_ID)-$(PROJECT_NAME)-$(ENV)-logs,OTEL_INSTRUMENTATION_GENAI_CAPTURE_MESSAGE_CONTENT=NO_CONTENT" \
		$(if $(IAP),--iap) \
		$(if $(PORT),--port=$(PORT))

local-backend:
	uv run uvicorn app.fast_api_app:app --host localhost --port $(or $(PORT),8000) --reload

# Legacy target, calling the new generic one
setup-dev-env:
	$(MAKE) tf-init ENV=dev
	$(MAKE) tf-apply ENV=dev

