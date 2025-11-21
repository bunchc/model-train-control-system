.PHONY: help install dev-install lint format format-check type-check security test test-unit test-integration test-e2e coverage docker-build docker-scan check ci all clean

# Default target
help:
	@echo "Model Train Control System - Central API"
	@echo ""
	@echo "Available targets:"
	@echo "  install        - Install production dependencies"
	@echo "  dev-install    - Install development dependencies"
	@echo "  lint           - Run ruff linter checks"
	@echo "  format         - Format code with ruff"
	@echo "  format-check   - Check code formatting without modifying"
	@echo "  type-check     - Run mypy type checker"
	@echo "  security       - Run security scans (bandit + safety)"
	@echo "  test           - Run all tests"
	@echo "  test-unit      - Run unit tests only"
	@echo "  test-integration - Run integration tests only"
	@echo "  test-e2e       - Run E2E tests only"
	@echo "  coverage       - Run tests with coverage report"
	@echo "  docker-build   - Build Docker image"
	@echo "  docker-scan    - Scan Docker image for vulnerabilities"
	@echo "  check          - Run all quality & security checks (fast)"
	@echo "  ci             - CI pipeline (format-check, lint, type-check, security, test)"
	@echo "  all            - Run all checks, tests, and coverage"
	@echo "  clean          - Remove generated files and caches"

# Dependencies
install:
	@echo "Installing production dependencies..."
	pip install -r requirements.txt

dev-install:
	@echo "Installing development dependencies..."
	pip install -r requirements.txt
	pip install -e .
	pip install pytest pytest-cov pytest-asyncio pytest-mock ruff mypy bandit[toml] safety types-PyYAML

# Linting
lint:
	@echo "Running ruff linter..."
	ruff check app/ tests/

# Formatting
format:
	@echo "Formatting code with ruff..."
	ruff format app/ tests/

format-check:
	@echo "Checking code formatting..."
	ruff format --check app/ tests/

# Type checking
type-check:
	@echo "Running mypy type checker..."
	mypy app/

# Security scanning
security: security-bandit security-safety
	@echo "✅ Security scans complete"

security-bandit:
	@echo "Running Bandit security scan..."
	@bandit -c pyproject.toml -r app/ -f screen
	@bandit -c pyproject.toml -r app/ -f json -o bandit-report.json

security-safety:
	@echo "Checking dependencies for vulnerabilities..."
	@safety check --file requirements.txt --output json > safety-report.json || true
	@safety check --file requirements.txt || true

# Testing
test:
	@echo "Running all tests..."
	pytest tests/ -v

test-unit:
	@echo "Running unit tests..."
	pytest tests/unit/ -v

test-integration:
	@echo "Running integration tests..."
	pytest tests/integration/ -v

test-e2e:
	@echo "Running E2E tests..."
	pytest tests/e2e/ -v

# Coverage
coverage:
	@echo "Running tests with coverage..."
	pytest tests/ -v --cov=app --cov-report=term-missing --cov-report=html --cov-report=xml

# Docker
docker-build:
	@echo "Building Docker image..."
	docker build -t central-api:local .

docker-scan: docker-build
	@echo "Scanning Docker image for vulnerabilities..."
	@command -v trivy >/dev/null 2>&1 || { echo "Trivy not installed. Install: https://github.com/aquasecurity/trivy"; exit 1; }
	trivy image central-api:local

# Quality gates
check: format-check lint type-check security
	@echo ""
	@echo "✅ All quality & security checks passed!"

ci: format-check lint type-check security test
	@echo ""
	@echo "✅ CI pipeline passed!"

# Run all checks
all: format lint type-check security test coverage
	@echo ""
	@echo "✅ All checks passed!"

# Clean up generated files
clean:
	@echo "Cleaning up generated files..."
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "htmlcov" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name ".coverage" -delete
	find . -type f -name "coverage.xml" -delete
	find . -type f -name "bandit-report.json" -delete
	find . -type f -name "safety-report.json" -delete
	rm -rf *.db test_*.db
	@echo "✅ Clean complete!"
