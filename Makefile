.PHONY: help install lint-docs lint-docs-fix lint-links check-docs clean-docs pre-commit-install pre-commit-run

# Default target
.DEFAULT_GOAL := help

# Colors for output
CYAN := \033[0;36m
GREEN := \033[0;32m
YELLOW := \033[0;33m
RED := \033[0;31m
RESET := \033[0m

help: ## Show this help message
	@echo "$(CYAN)Model Train Control System - Development Commands$(RESET)"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "$(GREEN)%-20s$(RESET) %s\n", $$1, $$2}'

install: ## Install all dependencies (Node.js + Python)
	@echo "$(CYAN)Installing dependencies...$(RESET)"
	npm install
	@echo "$(GREEN)Dependencies installed$(RESET)"

# ============================================================================
# Documentation Quality
# ============================================================================

.PHONY: lint-docs
lint-docs: ## Lint Markdown documentation
	@echo "$(CYAN)Linting Markdown files...$(RESET)"
	@npx markdownlint-cli2 "**/*.md" "#node_modules" "#**/node_modules" "#.venv" "#venv" "#build" "#dist" "#edge-controllers/pi-template/.venv"

.PHONY: lint-docs-fix
lint-docs-fix: ## Lint and auto-fix Markdown documentation
	@echo "$(CYAN)Linting and fixing Markdown files...$(RESET)"
	@npx markdownlint-cli2 --fix "**/*.md" "#node_modules" "#**/node_modules" "#.venv" "#venv" "#build" "#dist" "#edge-controllers/pi-template/.venv"

lint-links: ## Check Markdown links for validity
	@echo "$(CYAN)Checking Markdown links...$(RESET)"
	find . -name '*.md' \
		! -path '*/node_modules/*' \
		! -path '*/.venv/*' \
		! -path '*/venv/*' \
		-exec markdown-link-check --config .markdown-link-check.json {} \;

check-docs: lint-docs lint-links ## Run all documentation quality checks
	@echo "$(GREEN)Documentation checks passed!$(RESET)"

clean-docs: ## Clean documentation artifacts
	@echo "$(CYAN)Cleaning documentation artifacts...$(RESET)"
	find . -name '*.md.bak' -delete 2>/dev/null || true
	@echo "$(GREEN)Documentation cleanup complete$(RESET)"

# ============================================================================
# Pre-commit Hooks
# ============================================================================

pre-commit-install: ## Install pre-commit hooks
	@echo "$(CYAN)Installing pre-commit hooks...$(RESET)"
	pre-commit install
	pre-commit install --hook-type commit-msg
	@echo "$(GREEN)Pre-commit hooks installed$(RESET)"

pre-commit-run: ## Run pre-commit on all files
	@echo "$(CYAN)Running pre-commit on all files...$(RESET)"
	pre-commit run --all-files

# ============================================================================
# Project-wide commands
# ============================================================================

clean: clean-docs ## Clean all build artifacts and caches
	@echo "$(CYAN)Cleaning project...$(RESET)"
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "htmlcov" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name ".coverage" -delete 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	@echo "$(GREEN)Cleanup complete$(RESET)"

# ============================================================================
# Edge Controllers
# ============================================================================

edge-check: ## Run edge controller quality checks
	@echo "$(CYAN)Running edge controller checks...$(RESET)"
	cd edge-controllers/pi-template && $(MAKE) check

edge-test: ## Run edge controller tests
	@echo "$(CYAN)Running edge controller tests...$(RESET)"
	cd edge-controllers/pi-template && $(MAKE) test

edge-coverage: ## Run edge controller tests with coverage
	@echo "$(CYAN)Running edge controller coverage...$(RESET)"
	cd edge-controllers/pi-template && $(MAKE) coverage

# ============================================================================
# Full validation
# ============================================================================

check-all: check-docs edge-check ## Run all quality checks (docs + edge)
	@echo "$(GREEN)All checks passed!$(RESET)"

# ============================================================================
# Local GitHub Actions Testing (act)
# ============================================================================

.PHONY: act-install act-list act-test-build act-test-workflows

act-install: ## Install act for local GitHub Actions testing
	@echo "$(CYAN)Installing act...$(RESET)"
	@if command -v brew >/dev/null 2>&1; then \
		brew install act; \
	else \
		echo "$(RED)Homebrew not found. Install manually: https://github.com/nektos/act$(RESET)"; \
		exit 1; \
	fi
	@echo "$(GREEN)act installed. See docs/local-github-actions.md for usage$(RESET)"

act-list: ## List available GitHub Actions workflows
	@echo "$(CYAN)Available workflows:$(RESET)"
	@act -l || echo "$(YELLOW)act not installed. Run 'make act-install'$(RESET)"

act-test-build: ## Test Docker image builds locally
	@echo "$(CYAN)Testing Docker image builds with act...$(RESET)"
	@if ! command -v act >/dev/null 2>&1; then \
		echo "$(RED)act not installed. Run 'make act-install' first$(RESET)"; \
		exit 1; \
	fi
	act push -W .github/workflows/build-images.yml.local \
		-j build-central-api -j build-edge-controller

act-test-workflows: ## Dry-run all local workflows
	@echo "$(CYAN)Dry-run of all workflows...$(RESET)"
	@if ! command -v act >/dev/null 2>&1; then \
		echo "$(RED)act not installed. Run 'make act-install' first$(RESET)"; \
		exit 1; \
	fi
	act -n -W .github/workflows/build-images.yml.local

# ============================================================================
# Deployment (Ansible)
# ============================================================================

.PHONY: deploy-help deploy-provision deploy-central deploy-edge deploy-update deploy-status

deploy-help: ## Show deployment help
	@./scripts/deploy.sh help

deploy-provision: ## Provision Raspberry Pi devices (use HOST=rpi-train-01 to limit)
	@echo "$(CYAN)Provisioning Raspberry Pi devices...$(RESET)"
	@if [ -n "$(HOST)" ]; then \
		./scripts/deploy.sh provision $(HOST); \
	else \
		./scripts/deploy.sh provision; \
	fi

deploy-central: ## Deploy central infrastructure (API + MQTT)
	@echo "$(CYAN)Deploying central infrastructure...$(RESET)"
	@./scripts/deploy.sh central

deploy-edge: ## Deploy edge controllers (use HOST=rpi-train-01 to limit)
	@echo "$(CYAN)Deploying edge controllers...$(RESET)"
	@if [ -n "$(HOST)" ]; then \
		./scripts/deploy.sh edge $(HOST); \
	else \
		./scripts/deploy.sh edge; \
	fi

deploy-update: ## Update deployments (use COMPONENT=edge or central)
	@echo "$(CYAN)Updating deployments...$(RESET)"
	@./scripts/deploy.sh update $(COMPONENT)

deploy-status: ## Check deployment status
	@echo "$(CYAN)Checking deployment status...$(RESET)"
	@./scripts/deploy.sh status
