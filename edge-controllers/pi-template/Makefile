.PHONY: help install dev-install format lint type-check test test-unit test-integration test-e2e test-fast coverage clean check all

# Default target
.DEFAULT_GOAL := help

# Colors for output
CYAN := \033[0;36m
GREEN := \033[0;32m
YELLOW := \033[0;33m
RED := \033[0;31m
RESET := \033[0m

help: ## Show this help message
	@echo "$(CYAN)Edge Controller - Development Commands$(RESET)"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "$(GREEN)%-20s$(RESET) %s\n", $$1, $$2}'

install: ## Install production dependencies
	@echo "$(CYAN)Installing production dependencies...$(RESET)"
	pip install -r requirements.txt

dev-install: ## Install development dependencies
	@echo "$(CYAN)Installing development dependencies...$(RESET)"
	pip install -e ".[dev]"

format: ## Format code with ruff
	@echo "$(CYAN)Formatting code...$(RESET)"
	ruff format app/ tests/

format-check: ## Check code formatting without making changes
	@echo "$(CYAN)Checking code format...$(RESET)"
	ruff format --check app/ tests/

lint: ## Run ruff linter
	@echo "$(CYAN)Running linter...$(RESET)"
	ruff check app/ tests/

lint-fix: ## Run ruff linter and fix issues
	@echo "$(CYAN)Running linter with auto-fix...$(RESET)"
	ruff check --fix app/ tests/

type-check: ## Run mypy type checker
	@echo "$(CYAN)Running type checker...$(RESET)"
	mypy app/

test-unit: ## Run unit tests only
	@echo "$(CYAN)Running unit tests...$(RESET)"
	pytest -v -m unit tests/unit/

test-integration: ## Run integration tests only
	@echo "$(CYAN)Running integration tests...$(RESET)"
	pytest -v -m integration tests/integration/

test-e2e: ## Run end-to-end tests only
	@echo "$(CYAN)Running E2E tests...$(RESET)"
	pytest -v -m e2e tests/e2e/

test-fast: ## Run only fast unit tests
	@echo "$(CYAN)Running fast tests...$(RESET)"
	pytest -v -m "unit and not slow" tests/unit/

test: ## Run all tests
	@echo "$(CYAN)Running all tests...$(RESET)"
	pytest -v tests/

coverage: ## Run tests with coverage report
	@echo "$(CYAN)Running tests with coverage...$(RESET)"
	pytest -v --cov --cov-report=term-missing --cov-report=html
	@echo "$(GREEN)Coverage report generated in htmlcov/index.html$(RESET)"

clean: ## Clean up cache and build artifacts
	@echo "$(CYAN)Cleaning up...$(RESET)"
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "htmlcov" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name ".coverage" -delete 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	@echo "$(GREEN)Cleanup complete$(RESET)"

check: format-check lint type-check test-fast ## Run all quality checks (fast)
	@echo "$(GREEN)All checks passed!$(RESET)"

all: format lint type-check test coverage ## Run all checks and tests
	@echo "$(GREEN)All tasks completed successfully!$(RESET)"

ci: format-check lint type-check test ## CI pipeline (no formatting, all tests)
	@echo "$(GREEN)CI pipeline passed!$(RESET)"
