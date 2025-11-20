.PHONY: help install dev-install format lint type-check security test test-unit test-integration test-e2e test-fast coverage clean check all

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

security: ## Run all security scans
	@echo "$(CYAN)Running security scans...$(RESET)"
	@echo "$(YELLOW)Bandit (Security Linting)...$(RESET)"
	bandit -c pyproject.toml -r app/
	@echo "$(YELLOW)Safety (Dependency Vulnerabilities)...$(RESET)"
	safety check
	@echo "$(GREEN)Security scans complete$(RESET)"

security-bandit: ## Run Bandit security scan
	@echo "$(CYAN)Running Bandit security scan...$(RESET)"
	bandit -c pyproject.toml -r app/ -f screen
	bandit -c pyproject.toml -r app/ -f json -o bandit-report.json

security-safety: ## Check dependencies for vulnerabilities
	@echo "$(CYAN)Checking dependencies for vulnerabilities...$(RESET)"
	safety check --json --output safety-report.json
	safety check

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
	rm -f bandit-report.json safety-report.json mypy-report.xml
	@echo "$(GREEN)Cleanup complete$(RESET)"

check: format-check lint type-check security test-fast ## Run all quality & security checks (fast)
	@echo "$(GREEN)All checks passed!$(RESET)"

all: format lint type-check security test coverage ## Run all checks, tests, and coverage
	@echo "$(GREEN)All tasks completed successfully!$(RESET)"

ci: format-check lint type-check security test ## CI pipeline (no formatting, all tests)
	@echo "$(GREEN)CI pipeline passed!$(RESET)"

docker-build: ## Build Docker image
	@echo "$(CYAN)Building Docker image...$(RESET)"
	docker build -t edge-controller:local .

docker-scan: docker-build ## Scan Docker image for vulnerabilities
	@echo "$(CYAN)Scanning Docker image...$(RESET)"
	docker run --rm -v /var/run/docker.sock:/var/run/docker.sock \
		aquasec/trivy image edge-controller:local

pre-commit-install: ## Install pre-commit hooks
	@echo "$(CYAN)Installing pre-commit hooks...$(RESET)"
	pre-commit install
	pre-commit install --hook-type commit-msg
	@echo "$(GREEN)Pre-commit hooks installed$(RESET)"

pre-commit-run: ## Run pre-commit on all files
	@echo "$(CYAN)Running pre-commit on all files...$(RESET)"
	pre-commit run --all-files
