# Local GitHub Actions Testing with `act`

This guide shows how to test GitHub Actions workflows locally without pushing to GitHub.

---

## What is `act`?

[`act`](https://github.com/nektos/act) runs GitHub Actions locally using Docker. It reads your workflow files and executes them in containers that mimic GitHub's runners.

---

## Installation

### macOS (Homebrew)

```bash
brew install act
```

### Linux

```bash
curl -s https://raw.githubusercontent.com/nektos/act/master/install.sh | sudo bash
```

### Verify Installation

```bash
act --version
```

---

## Quick Start

### 1. List Available Workflows

```bash
# From repo root
act -l
```

### 2. Run a Specific Workflow

```bash
# Run workflow by event (e.g., push event)
act push

# Run a specific job
act -j build-central-api

# Run with specific event file
act pull_request
```

### 3. Dry Run (See What Would Execute)

```bash
act -n
```

---

## Docker Image Selection

`act` uses Docker images to simulate GitHub runners. Choose based on your needs:

### Option 1: Micro (Fast, Minimal) - **Recommended for Quick Tests**

```bash
act -P ubuntu-latest=node:16-buster-slim
```

- **Size:** ~150MB
- **Use case:** Simple jobs without many dependencies
- **Limitations:** Missing some tools (git, python might need manual install)

### Option 2: Medium (Balanced) - **Recommended for Most Workflows**

```bash
act -P ubuntu-latest=catthehacker/ubuntu:act-latest
```

- **Size:** ~500MB-1GB
- **Use case:** Most CI/CD workflows
- **Includes:** git, curl, wget, python, node, docker

### Option 3: Large (Full GitHub Runner) - **Use for Complex Workflows**

```bash
act -P ubuntu-latest=catthehacker/ubuntu:full-latest
```

- **Size:** ~18GB (first pull takes time)
- **Use case:** Workflows using many GitHub Actions
- **Identical to:** GitHub's actual `ubuntu-latest` runner

### Set Default (Create `.actrc`)

```bash
# In repo root
cat > .actrc << 'EOF'
-P ubuntu-latest=catthehacker/ubuntu:act-latest
--container-architecture linux/amd64
EOF
```

---

## Testing GHCR Build Workflow Locally

### Example: Build Docker Images Locally

```bash
# Run the build workflow
act push -j build-central-api

# Run with secrets (for GHCR login)
act push -j build-central-api \
  -s GITHUB_TOKEN="$(gh auth token)"

# Run without pushing (dry-run the build)
act push -j build-central-api \
  --env SKIP_PUSH=true
```

### Multi-Architecture Builds

**Note:** `act` runs on your local architecture. To test multi-arch builds (ARM64), you need:

```bash
# Set up QEMU for multi-arch (one-time setup)
docker run --rm --privileged multiarch/qemu-user-static --reset -p yes

# Then run workflow
act push -j build-edge-controller
```

---

## Local Testing Workflow Structure

For workflows that should be testable locally but disabled on GitHub, use this pattern:

### Workflow File: `.github/workflows/build-images.yml.local`

```yaml
name: Build Docker Images (Local Testing Only)

# This workflow is DISABLED on GitHub (use .local extension)
# Run locally with: act push -W .github/workflows/build-images.yml.local

on:
  push:
    branches: [main, feat/*]
  workflow_dispatch:  # Manual trigger

env:
  REGISTRY: ghcr.io
  SKIP_PUSH: ${{ github.event_name == 'push' && github.ref != 'refs/heads/main' }}

jobs:
  build-central-api:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v3

      - name: Build central API image
        uses: docker/build-push-action@v5
        with:
          context: ./central_api
          file: ./central_api/Dockerfile
          push: false  # Don't push when testing locally
          tags: |
            ${{ env.REGISTRY }}/${{ github.repository }}/central-api:test
          load: true  # Load into local Docker

      - name: Test image
        run: |
          docker run --rm \
            ${{ env.REGISTRY }}/${{ github.repository }}/central-api:test \
            python -c "import app; print('Import successful')"

  build-edge-controller:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Set up QEMU
        uses: docker/setup-qemu-action@v3

      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v3

      - name: Build edge controller image (multi-arch)
        uses: docker/build-push-action@v5
        with:
          context: ./edge-controllers/pi-template
          file: ./edge-controllers/pi-template/Dockerfile
          platforms: linux/amd64,linux/arm64
          push: false
          tags: |
            ${{ env.REGISTRY }}/${{ github.repository }}/edge-controller:test
```

---

## Common Use Cases

### 1. Test Build Before Committing

```bash
# Test if your Dockerfiles build successfully
act -j build-central-api -j build-edge-controller
```

### 2. Test With Secrets

```bash
# Use GitHub CLI to get token
act push -s GITHUB_TOKEN="$(gh auth token)"

# Or use .secrets file
cat > .secrets << 'EOF'
GITHUB_TOKEN=ghp_your_token_here
MQTT_PASSWORD=your_password
EOF

act push --secret-file .secrets
```

**Important:** Add `.secrets` to `.gitignore`!

### 3. Test Specific Event Payloads

```bash
# Create event payload
cat > event.json << 'EOF'
{
  "pull_request": {
    "number": 123,
    "head": {"ref": "feat/deployment"}
  }
}
EOF

act pull_request -e event.json
```

### 4. Debug Failed Jobs

```bash
# Run with verbose output
act -v

# Run and keep containers for inspection
act --rm=false

# Then inspect
docker ps -a
docker logs <container_id>
```

---

## Limitations of `act`

### What Works ✅

- Most `uses:` actions from GitHub Marketplace
- Environment variables and secrets
- Matrix builds
- Docker builds and runs
- Checkout, cache, and artifact actions (with local paths)

### What Doesn't Work ❌

- GitHub-specific features (GitHub API integrations)
- Actual pushes to GHCR (unless you provide credentials)
- Some hosted runners' pre-installed tools
- Nested workflows (`workflow_call`)

### Workarounds

```yaml
# Skip steps that don't work in act
- name: Push to registry
  if: ${{ !env.ACT }}  # Only run on GitHub
  run: docker push ...

- name: Local build only
  if: ${{ env.ACT }}  # Only run in act
  run: docker build ...
```

---

## Recommended Workflow: Disable on GitHub, Test Locally

### Directory Structure

```
.github/
  ├── workflows/
  │   ├── build-images.yml.local      # Test with act
  │   ├── deploy.yml.local            # Test with act
  │   └── disabled/                   # Old workflows
  │       ├── ci.yml.disabled
  │       └── ...
  └── act-config/
      ├── .actrc                      # act configuration
      └── event-payloads/             # Test event data
          ├── push.json
          └── pull_request.json
```

### Makefile Integration

```makefile
# Add to root Makefile
.PHONY: test-workflows
test-workflows: ## Test GitHub Actions locally with act
 @echo "$(CYAN)Testing workflows locally...$(RESET)"
 act -l  # List workflows
 act -n  # Dry run

.PHONY: test-build-images
test-build-images: ## Build Docker images locally
 @echo "$(CYAN)Building images with act...$(RESET)"
 act push -W .github/workflows/build-images.yml.local \
  -j build-central-api \
  -j build-edge-controller
```

---

## GitHub Actions: Disabled Until Refactor

### Current State

All workflows are disabled (`.yml.disabled` extension) per project plan:

- `ci.yml.disabled`
- `ci-central-api.yml.disabled`
- `ci-docs.yml.disabled`
- `ci-security.yml.disabled`
- `pre-commit-ci.yml.disabled`

### Re-enabling Workflow (When Ready)

```bash
# Remove .disabled extension
mv .github/workflows/ci.yml.disabled .github/workflows/ci.yml

# Or keep disabled but test locally
act -W .github/workflows/ci.yml.disabled
```

---

## Best Practices

### 1. Use `.local` Extension for Test Workflows

```
build-images.yml.local   # Won't run on GitHub
```

### 2. Add `.actrc` to Repo Root

```bash
# .actrc
-P ubuntu-latest=catthehacker/ubuntu:act-latest
--container-architecture linux/amd64
--artifact-server-path /tmp/artifacts
```

### 3. Add to `.gitignore`

```gitignore
# act local testing
.secrets
.env.act
event.json
```

### 4. Document in README

```markdown
## Testing CI Locally

We use `act` to test GitHub Actions locally:

\`\`\`bash
# Install act
brew install act

# Test workflows
make test-workflows
\`\`\`
```

---

## Example: Complete Local Test Cycle

```bash
# 1. Install act
brew install act

# 2. Configure act
cat > .actrc << 'EOF'
-P ubuntu-latest=catthehacker/ubuntu:act-latest
EOF

# 3. List available jobs
act -l

# 4. Test build workflow (dry run)
act push -n -W .github/workflows/build-images.yml.local

# 5. Actually build images
act push -W .github/workflows/build-images.yml.local

# 6. Verify images in local Docker
docker images | grep central-api
docker images | grep edge-controller

# 7. Test the built images
docker run --rm ghcr.io/bunchc/model-train-control-system/central-api:test \
  python -c "from app import main; print('Success')"
```

---

## Troubleshooting

### Issue: "Container failed to start"

```bash
# Check Docker is running
docker ps

# Use smaller image
act -P ubuntu-latest=node:16-buster-slim

# Check logs
act -v
```

### Issue: "Permission denied" errors

```bash
# Run with user namespace mapping
act --userns

# Or run Docker daemon in rootless mode
```

### Issue: "Out of disk space"

```bash
# Clean up act containers
docker ps -a | grep act | awk '{print $1}' | xargs docker rm

# Clean up images
docker images | grep act | awk '{print $3}' | xargs docker rmi
```

---

## References

- [act GitHub Repository](https://github.com/nektos/act)
- [act Documentation](https://nektosact.com/)
- [Docker Images for act](https://github.com/catthehacker/docker_images)
- [GitHub Actions Documentation](https://docs.github.com/en/actions)

---

## Next Steps

1. **Install act:** `brew install act`
2. **Create `.actrc`:** Configure default runner image
3. **Create test workflow:** `.github/workflows/build-images.yml.local`
4. **Test locally:** `act push -W .github/workflows/build-images.yml.local`
5. **Add to Makefile:** `make test-workflows` target
6. **Document:** Update main README with local testing instructions

**Status:** Ready to create local-testable workflows ✅
