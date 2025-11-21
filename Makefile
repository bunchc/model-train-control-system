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
