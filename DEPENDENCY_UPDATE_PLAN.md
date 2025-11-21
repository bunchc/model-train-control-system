# Dependency Update Plan

**Branch:** `chore/dependency-updates`  
**Created:** November 21, 2025  
**Status:** 🚧 In Progress

## ✅ Completed: CI/CD Updates (Low Risk)

All GitHub Actions have been updated and merged to main:

- ✅ #5: actions/setup-python (4 → 6)
- ✅ #4: actions/setup-node (4 → 6)
- ✅ #3: actions/checkout (4 → 6)
- ✅ #2: codecov/codecov-action (4 → 5)
- ✅ #1: github/codeql-action (3 → 4)

---

## 📋 Phase 1: Python Dependencies (Medium Risk)

**Strategy:** Update, test, commit in batches by impact level

### 1.1 Low-Impact Python Updates (Merge First)

```bash
# Type stubs and development tools
gh pr merge 14 --squash  # types-requests (2.31.0 → 2.32.3)
gh pr merge 13 --squash  # pytest-cov (5.0.0 → 6.0.0)
gh pr merge 9  --squash  # pytest-asyncio (0.23.6 → 0.26.0)
```

**Testing:**

```bash
cd central_api
make test
```

### 1.2 Medium-Impact Python Updates (Test Carefully)

```bash
# Testing framework
gh pr merge 22 --squash  # pytest (8.1.1 → 8.4.2)

# Type checking
gh pr merge 12 --squash  # mypy (1.9.0 → 1.18.1)

# Security scanning
gh pr merge 17 --squash  # safety (3.1.0 → 3.7.0)
```

**Testing:**

```bash
cd central_api
make test
make lint
cd ../edge-controllers/pi-template
make test
```

### 1.3 High-Impact Python Updates (Requires API Review)

```bash
# Core framework
gh pr merge 21 --squash  # fastapi (0.110.0 → 0.121.3)

# HTTP client
gh pr merge 24 --squash  # requests (2.26.0 → 2.32.5)

# ASGI server
gh pr merge 8  --squash  # uvicorn (0.29.0 → 0.34.0)
```

**Testing:**

```bash
# Full integration test
cd central_api
make test
python -m pytest tests/e2e/ -v

# Manual API testing
uvicorn app.main:app --reload
# Test endpoints at http://localhost:8000/docs
```

**Risk Assessment:**

- FastAPI 0.110.0 → 0.121.3 may have breaking changes in Pydantic v2 integration
- Check release notes: https://github.com/tiangolo/fastapi/releases

---

## 📦 Phase 2: Node/Frontend Dependencies (Medium-High Risk)

**Strategy:** Update non-breaking changes first, then handle React 19

### 2.1 Safe Node Updates

```bash
# MQTT library (major version - test carefully)
gh pr merge 27 --squash  # mqtt (4.3.8 → 5.14.1)
gh pr merge 6  --squash  # mqtt in gateway (4.3.8 → 5.14.1)

# Development dependencies
gh pr merge 23 --squash  # @types/react-dom (17.0.26 → 19.0.4)
gh pr merge 16 --squash  # @types/react (17.0.83 → 19.0.4)
gh pr merge 15 --squash  # typescript (4.9.5 → 5.7.3)
```

**Testing:**

```bash
cd frontend/web
npm install
npm run build
npm start
# Verify UI loads and MQTT connection works
```

### 2.2 React 19 Migration (⚠️ Breaking Changes)

```bash
# DO NOT auto-merge - requires code changes
# PR #20: react (17.0.2 → 19.2.0)
# PR #26: react-dom (17.0.2 → 19.2.0)
# PR #25: react-scripts (4.0.3 → 5.0.1)
```

**Migration Steps:**

1. **Review React 19 breaking changes:**
   - https://react.dev/blog/2024/04/25/react-19-upgrade-guide
   - New hooks API changes
   - Server Components considerations

2. **Update code:**

   ```bash
   cd frontend/web
   # Manually merge the PRs or cherry-pick changes
   npm install react@19 react-dom@19
   npm install react-scripts@5
   ```

3. **Fix breaking changes:**
   - Update `src/components/Dashboard.tsx`
   - Update `src/App.tsx`
   - Check for deprecated lifecycle methods
   - Update event handler types

4. **Test thoroughly:**

   ```bash
   npm run build
   npm test
   npm start
   ```

### 2.3 Other Node Updates

```bash
# Gateway dependencies
gh pr merge 11 --squash  # express (4.21.2 → 5.0.1)
gh pr merge 10 --squash  # body-parser (1.20.3 → 1.21.0)
gh pr merge 7  --squash  # nodemon (2.0.22 → 3.1.9)
```

**Testing:**

```bash
cd gateway/orchestrator
npm install
npm start
# Test MQTT/HTTP bridge functionality
```

---

## 🐳 Phase 3: Docker Base Images (⚠️ HIGH RISK)

**DO NOT merge until extensively tested!**

### Python 3.9 → 3.14 Migration

```bash
# PR #19: central_api/Dockerfile
# PR #18: edge-controllers/pi-template/Dockerfile
```

**Breaking Changes:**

- Python 3.14 is a MAJOR version jump (skipping 3.10, 3.11, 3.12, 3.13)
- Potential incompatibilities with dependencies
- May require code changes for deprecated features

**Migration Strategy:**

1. **Create test branch:**

   ```bash
   git checkout -b test/python-3.14
   ```

2. **Update one Dockerfile at a time:**

   ```dockerfile
   # Test with intermediate versions first
   FROM python:3.10-slim  # Test
   FROM python:3.11-slim  # Test
   FROM python:3.12-slim  # Test
   FROM python:3.13-slim  # Test
   FROM python:3.14-slim  # Final
   ```

3. **Test each step:**

   ```bash
   cd central_api
   docker build -t central-api:py3.14 .
   docker run -it central-api:py3.14 python --version
   docker run -it central-api:py3.14 pytest tests/
   ```

4. **Check for deprecation warnings:**

   ```bash
   python -W error::DeprecationWarning -m pytest
   ```

5. **Update pyproject.toml:**

   ```toml
   [tool.poetry.dependencies]
   python = "^3.14"
   ```

**Testing Checklist:**

- [ ] All unit tests pass
- [ ] All integration tests pass
- [ ] Docker image builds successfully
- [ ] Container starts without errors
- [ ] API endpoints respond correctly
- [ ] MQTT connections work
- [ ] No deprecation warnings
- [ ] Performance is acceptable

---

## 📊 Execution Order

### Week 1: Python Backend

1. ✅ Merge CI/CD updates (DONE)
2. 🔄 Merge low-impact Python deps
3. 🔄 Test & merge medium-impact Python deps
4. 🔄 Carefully review & merge high-impact Python deps (FastAPI, requests, uvicorn)

### Week 2: Frontend

1. 🔄 Merge safe Node deps (MQTT, types, TypeScript)
2. 🔄 Test React 19 migration locally
3. 🔄 Apply React 19 code fixes
4. 🔄 Merge React 19 updates
5. 🔄 Merge gateway Node deps

### Week 3: Docker (or later)

1. 🔄 Research Python 3.14 compatibility
2. 🔄 Test incrementally (3.10 → 3.11 → 3.12 → 3.13 → 3.14)
3. 🔄 Fix any breaking changes
4. 🔄 Merge Docker updates

---

## 🚀 Quick Start Commands

```bash
# Ensure you're on the dependency update branch
git checkout chore/dependency-updates
git pull origin main

# Start with Phase 1.1 (Low-Impact Python)
gh pr merge 14 --squash
gh pr merge 13 --squash
gh pr merge 9 --squash

# Test
cd central_api && make test && cd ..

# Commit if tests pass
git add -A
git commit -m "chore(deps): Update low-impact Python dependencies"
git push origin chore/dependency-updates

# Continue with Phase 1.2, 1.3, etc.
```

---

## 📝 Notes

- **Always run tests before committing**
- **Update CHANGELOG.md** for each phase
- **Create separate PRs** for Python, Node, and Docker updates
- **Monitor CI/CD pipelines** after each merge
- **Rollback plan:** Keep `main` branch stable; test in feature branches

---

## 🔗 Useful Links

- [FastAPI Releases](https://github.com/tiangolo/fastapi/releases)
- [React 19 Upgrade Guide](https://react.dev/blog/2024/04/25/react-19-upgrade-guide)
- [Python 3.14 Release Notes](https://docs.python.org/3.14/whatsnew/3.14.html)
- [Dependabot PR List](https://github.com/bunchc/model-train-control-system/pulls)
