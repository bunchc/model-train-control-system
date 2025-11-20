#!/bin/bash
# Git pre-commit hook to run quality checks

set -e

echo "Running pre-commit checks..."

# Format check
echo "Checking code format..."
ruff format --check app/ tests/ || {
    echo "Code format check failed. Run 'make format' to fix."
    exit 1
}

# Lint
echo "Running linter..."
ruff check app/ tests/ || {
    echo "Linting failed. Run 'make lint-fix' to attempt auto-fix."
    exit 1
}

# Type check
echo "Running type checker..."
mypy app/ || {
    echo "Type checking failed."
    exit 1
}

# Fast tests
echo "Running fast tests..."
pytest -v -m "unit and not slow" tests/unit/ || {
    echo "Tests failed."
    exit 1
}

echo "✓ All pre-commit checks passed!"
