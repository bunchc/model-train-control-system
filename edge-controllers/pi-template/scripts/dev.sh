#!/bin/bash
# Development utility script for edge controller

set -e

# Colors
CYAN='\033[0;36m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
RED='\033[0;31m'
RESET='\033[0m'

# Print colored message
print_msg() {
    echo -e "${CYAN}$1${RESET}"
}

print_success() {
    echo -e "${GREEN}✓ $1${RESET}"
}

print_error() {
    echo -e "${RED}✗ $1${RESET}"
}

# Show help
show_help() {
    cat << EOF
$(print_msg "Edge Controller - Development Commands")

Usage: ./scripts/dev.sh [command]

Commands:
    install         Install production dependencies
    dev-install     Install development dependencies
    format          Format code with ruff
    format-check    Check code formatting
    lint            Run ruff linter
    lint-fix        Run linter with auto-fix
    type-check      Run mypy type checker
    test            Run all tests
    test-unit       Run unit tests only
    test-integration Run integration tests only
    test-e2e        Run E2E tests only
    test-fast       Run fast unit tests only
    coverage        Run tests with coverage
    check           Run all quality checks (fast)
    all             Run all checks and tests
    clean           Clean cache and build artifacts
    help            Show this help message

EOF
}

# Install dependencies
install() {
    print_msg "Installing production dependencies..."
    pip install -r requirements.txt
    print_success "Dependencies installed"
}

dev_install() {
    print_msg "Installing development dependencies..."
    pip install -e ".[dev]"
    print_success "Development dependencies installed"
}

# Format code
format_code() {
    print_msg "Formatting code..."
    ruff format app/ tests/
    print_success "Code formatted"
}

format_check() {
    print_msg "Checking code format..."
    if ruff format --check app/ tests/; then
        print_success "Code format is correct"
    else
        print_error "Code format check failed"
        exit 1
    fi
}

# Lint code
lint_code() {
    print_msg "Running linter..."
    if ruff check app/ tests/; then
        print_success "Linting passed"
    else
        print_error "Linting failed"
        exit 1
    fi
}

lint_fix() {
    print_msg "Running linter with auto-fix..."
    ruff check --fix app/ tests/
    print_success "Linting complete"
}

# Type check
type_check() {
    print_msg "Running type checker..."
    if mypy app/; then
        print_success "Type checking passed"
    else
        print_error "Type checking failed"
        exit 1
    fi
}

# Run tests
run_tests() {
    print_msg "Running all tests..."
    if pytest -v tests/; then
        print_success "All tests passed"
    else
        print_error "Tests failed"
        exit 1
    fi
}

run_unit_tests() {
    print_msg "Running unit tests..."
    if pytest -v -m unit tests/unit/; then
        print_success "Unit tests passed"
    else
        print_error "Unit tests failed"
        exit 1
    fi
}

run_integration_tests() {
    print_msg "Running integration tests..."
    if pytest -v -m integration tests/integration/; then
        print_success "Integration tests passed"
    else
        print_error "Integration tests failed"
        exit 1
    fi
}

run_e2e_tests() {
    print_msg "Running E2E tests..."
    if pytest -v -m e2e tests/e2e/; then
        print_success "E2E tests passed"
    else
        print_error "E2E tests failed"
        exit 1
    fi
}

run_fast_tests() {
    print_msg "Running fast tests..."
    if pytest -v -m "unit and not slow" tests/unit/; then
        print_success "Fast tests passed"
    else
        print_error "Fast tests failed"
        exit 1
    fi
}

# Coverage
run_coverage() {
    print_msg "Running tests with coverage..."
    if pytest -v --cov --cov-report=term-missing --cov-report=html; then
        print_success "Coverage report generated in htmlcov/index.html"
    else
        print_error "Coverage generation failed"
        exit 1
    fi
}

# Clean
clean() {
    print_msg "Cleaning up..."
    find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
    find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
    find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
    find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
    find . -type d -name "htmlcov" -exec rm -rf {} + 2>/dev/null || true
    find . -type f -name ".coverage" -delete 2>/dev/null || true
    find . -type f -name "*.pyc" -delete 2>/dev/null || true
    print_success "Cleanup complete"
}

# Run all quality checks
check() {
    format_check
    lint_code
    type_check
    run_fast_tests
    print_success "All quality checks passed!"
}

# Run everything
all() {
    format_code
    lint_code
    type_check
    run_tests
    run_coverage
    print_success "All tasks completed successfully!"
}

# Main script
case "${1:-help}" in
    install)
        install
        ;;
    dev-install)
        dev_install
        ;;
    format)
        format_code
        ;;
    format-check)
        format_check
        ;;
    lint)
        lint_code
        ;;
    lint-fix)
        lint_fix
        ;;
    type-check)
        type_check
        ;;
    test)
        run_tests
        ;;
    test-unit)
        run_unit_tests
        ;;
    test-integration)
        run_integration_tests
        ;;
    test-e2e)
        run_e2e_tests
        ;;
    test-fast)
        run_fast_tests
        ;;
    coverage)
        run_coverage
        ;;
    check)
        check
        ;;
    all)
        all
        ;;
    clean)
        clean
        ;;
    help|*)
        show_help
        ;;
esac
