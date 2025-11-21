# Edge Controller Testing

## Quick quality check (runs in <5 seconds)

make check

## Full test suite with coverage

make all

## Individual commands

make format
make lint
make type-check
make test-unit
make coverage

## Using shell script

./scripts/dev.sh check
./scripts/dev.sh all

## Install pre-commit hook

cp scripts/pre-commit.sh .git/hooks/pre-commit
chmod +x .git/hooks/pre-commit
