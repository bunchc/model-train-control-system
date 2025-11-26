# End of Day Status - November 24, 2025

## Current Branch

`feat/deployment-automation`

## Summary

Today we completed the design and implementation of Ansible-based deployment automation for the Model Train Control System. All infrastructure code is written and ready for testing, but actual deployment has not yet occurred.

---

## ✅ Completed Today

### 1. Research & Design Phase

- **Deployment Research**: Evaluated 5 approaches (Ansible, Docker Compose+Scripts, K3s, Terraform, Balena)
  - File: `docs/deployment-research.md`
  - **Decision**: Selected Ansible (scored 122/140) for best balance of simplicity and capabilities

- **Architectural Decisions**: Made key infrastructure choices
  - File: `docs/deployment-decisions.md`
  - Secrets: Ansible Vault (Phase 1) → HashiCorp Vault (Phase 2)
  - Registry: GitHub Container Registry (GHCR)
  - Network: Static IPs (production), mDNS (staging)
  - Logging: Deferred Loki stack to Phase 2

### 2. Ansible Infrastructure Implementation

Created complete Ansible deployment system in `infra/ansible/`:

**Playbooks** (`playbooks/`):

- `provision_pi.yml` - Provision fresh Raspberry Pi devices (Docker, mDNS, GPIO setup)
- `deploy_central.yml` - Deploy central_api + Mosquitto MQTT to central host
- `deploy_edge.yml` - Deploy edge-controller containers to RPi devices
- `update.yml` - Update existing deployments with new images
- `rollback.yml` - Rollback to previous container versions

**Inventories** (`inventory/`):

- `production/hosts.yml` - Production configuration (localhost + 192.168.1.214)
- `staging/hosts.yml` - Staging configuration (mDNS hostnames)

**Secrets** (`secrets/`):

- `vault.yml.example` - Template for encrypted secrets (NOT YET CREATED)
- `README.md` - Secrets management documentation

**Configuration**:

- `ansible.cfg` - Optimized for edge deployment (timeouts, retries, etc.)

### 3. Plugin System Refactoring

- **Removed**: Hardcoded `train_id` values (e.g., `train-001`)
- **Added**: UUID auto-generation logic in `deploy_edge.yml`
  - Generates UUID on first deployment if not in inventory
  - Saves UUID back to inventory file for persistence

- **Removed**: Redundant `has_gpio` flag
- **Added**: `hardware_type` parameter that determines both plugin and GPIO requirements
  - `stepper_hat`: Waveshare Stepper Motor HAT (`app/stepper_hat.py`) - **requires GPIO**
  - `generic`: Generic PWM GPIO controller (`app/hardware.py`) - **requires GPIO**
  - `simulator`: No-op simulator (`app/main.py`) - **no GPIO needed**

### 4. Documentation

Created comprehensive deployment documentation:

- `docs/deployment-runbook.md` - Complete operational guide
- `docs/local-github-actions.md` - Guide for testing GitHub Actions with `act`
- `docs/DEPLOYMENT_SUMMARY.md` - Quick reference
- `infra/ansible/secrets/README.md` - Secrets management guide

### 5. Supporting Tools

- **Updated** `scripts/deploy.sh` - Comprehensive Ansible wrapper with colored output
- **Updated** `Makefile` - Added deployment targets (deploy-central, deploy-edge, etc.)
- **Created** `.actrc` - Configuration for local GitHub Actions testing
- **Created** `.github/workflows/build-images.yml.local` - Multi-arch Docker builds (local only)

---

## 🚧 In Progress / Blocked

### Secrets Management (BLOCKED - User Input Required)

**Status**: Template created, vault NOT yet created  
**Location**: `infra/ansible/secrets/vault.yml` (does not exist yet)  
**Blocker**: Waiting for user to provide:

1. **GitHub Personal Access Token (PAT)**
   - URL: https://github.com/settings/tokens/new
   - Required scopes: `read:packages`, `write:packages`
   - Purpose: Authenticate to GitHub Container Registry (GHCR)

2. **MQTT Password**
   - Purpose: Secure MQTT broker authentication
   - Should be a strong random password

**Command to create vault** (once values are ready):

```bash
cd infra/ansible
ansible-vault create secrets/vault.yml
# Then paste the content from vault.yml.example and fill in real values
```

---

## ⏳ Not Started / Ready for Tomorrow

### Pre-Deployment Checklist

1. **Create Ansible Vault** (see above)
2. **Test SSH to RPi**: `ssh pi@192.168.1.214`
   - Ensure passwordless SSH is configured
   - If not, run: `ssh-copy-id pi@192.168.1.214`

### Deployment Sequence (Ready to Execute)

Once vault is created and SSH works:

```bash
# Step 1: Deploy central infrastructure (localhost)
./scripts/deploy.sh central
# Expected: Docker Compose deploys central_api + Mosquitto

# Step 2: Deploy edge controller (RPi at 192.168.1.214)
./scripts/deploy.sh edge
# Expected: Docker container deployed to RPi with stepper_hat plugin

# Step 3: Verify deployment
./scripts/deploy.sh status
# Expected: All containers running, health checks passing
```

**Alternative commands** (if you prefer direct Ansible):

```bash
cd infra/ansible

# Deploy central
ansible-playbook playbooks/deploy_central.yml --ask-vault-pass

# Deploy edge
ansible-playbook playbooks/deploy_edge.yml --ask-vault-pass

# Check status
ansible edge -m shell -a "docker ps" --ask-vault-pass
```

---

## 📋 Current Configuration

### Production Inventory (`infra/ansible/inventory/production/hosts.yml`)

**Central Host** (localhost):

- Components: `central_api` + `mqtt` (Mosquitto)
- Architecture: x86_64 (amd64)
- Connection: `ansible_connection: local`
- Ports: API=8000, MQTT=1883, WebSocket=9001

**Edge Host** (rpi-train-01):

- IP: `192.168.1.214`
- User: `pi`
- train_id: **Auto-generated UUID** (will be saved to inventory on first deploy)
- Plugin: `hardware_type: stepper_hat` (Waveshare Stepper Motor HAT)
- GPIO: Enabled automatically (derived from `hardware_type != 'simulator'`)

---

## 🔧 Technical Details

### Hardware Type → GPIO Mapping

The system now automatically derives GPIO requirements from `hardware_type`:

```yaml
# In inventory
hardware_type: stepper_hat  # or: generic, simulator

# Ansible derives:
- GPIO required: hardware_type != 'simulator'
- Privileged mode: hardware_type != 'simulator'
- Device mount: /dev/gpiomem (if GPIO required)
- Config value: gpio_enabled = true/false
```

### UUID Generation Logic

On first deployment to a new edge device:

1. Ansible checks if `train_id` is defined in inventory
2. If not, generates UUID: `{{ lookup('password', '/dev/null length=16 chars=hexdigits') | to_uuid }}`
3. Updates inventory file with generated UUID
4. Subsequent deployments reuse the persisted UUID

---

## 📁 Key Files Modified Today

```
docs/
  deployment-research.md          (NEW)
  deployment-decisions.md         (NEW)
  deployment-runbook.md           (NEW)
  local-github-actions.md         (NEW)
  DEPLOYMENT_SUMMARY.md           (NEW)

infra/ansible/
  ansible.cfg                     (NEW)
  inventory/
    production/hosts.yml          (NEW - configured for localhost + 192.168.1.214)
    staging/hosts.yml             (NEW)
  playbooks/
    provision_pi.yml              (NEW)
    deploy_central.yml            (NEW)
    deploy_edge.yml               (NEW - UUID + hardware_type logic)
    update.yml                    (NEW)
    rollback.yml                  (NEW)
  secrets/
    vault.yml.example             (NEW)
    README.md                     (NEW)

scripts/
  deploy.sh                       (REPLACED - now Ansible wrapper)

Makefile                          (UPDATED - added deployment targets)
.gitignore                        (UPDATED - added act entries)
.actrc                            (NEW)
.github/workflows/
  build-images.yml.local          (NEW)
```

---

## 🎯 Tomorrow's Action Plan

### Critical Path (Must Do)

1. **Obtain GitHub PAT** from https://github.com/settings/tokens/new
   - Scopes: `read:packages`, `write:packages`

2. **Choose MQTT password** (suggest using: `openssl rand -base64 32`)

3. **Create Ansible Vault**:

   ```bash
   cd infra/ansible
   ansible-vault create secrets/vault.yml
   # Use the password you'll remember or store in password manager
   ```

4. **Test SSH to RPi**:

   ```bash
   ssh pi@192.168.1.214
   # If fails, set up key: ssh-copy-id pi@192.168.1.214
   ```

5. **Deploy central infrastructure**:

   ```bash
   ./scripts/deploy.sh central
   ```

6. **Deploy edge controller**:

   ```bash
   ./scripts/deploy.sh edge
   ```

### Verification Steps

- [ ] `docker ps` on localhost shows `central_api` and `mosquitto` containers
- [ ] `curl http://localhost:8000/api/ping` returns success
- [ ] `ssh pi@192.168.1.214 "docker ps"` shows `edge-controller` container
- [ ] MQTT connection test: `mosquitto_sub -h localhost -p 1883 -t trains/# -u edge-controller -P <mqtt_password>`

### Optional / Nice to Have

- Test local GitHub Actions build: `act -l` (in repo root)
- Review and update documentation based on actual deployment experience
- Consider creating Phase 2 planning document for Loki logging stack

---

## 🐛 Known Issues / Considerations

1. **Container Images**:
   - We have NOT yet built the Docker images for this project
   - First deployment may fail if images don't exist in GHCR
   - May need to build and push images first: `act -W .github/workflows/build-images.yml.local`

2. **RPi State Unknown**:
   - Don't know if Docker is already installed on 192.168.1.214
   - May need to run `./scripts/deploy.sh provision` first

3. **Network Connectivity**:
   - Assuming RPi can reach localhost for MQTT/API
   - May need to update `central_api_host` and `mqtt_broker` if on different network

4. **Vault Password**:
   - Choose a strong password for the vault
   - Store it securely (password manager recommended)
   - You'll need it for every Ansible command with `--ask-vault-pass`

---

## 💡 Quick Reference Commands

```bash
# Create vault (interactive)
cd infra/ansible && ansible-vault create secrets/vault.yml

# Edit vault
ansible-vault edit infra/ansible/secrets/vault.yml

# View vault
ansible-vault view infra/ansible/secrets/vault.yml

# Deploy central (localhost)
./scripts/deploy.sh central

# Deploy edge (RPi)
./scripts/deploy.sh edge

# Provision new RPi
./scripts/deploy.sh provision

# Update deployments
./scripts/deploy.sh update

# Check status
./scripts/deploy.sh status

# Rollback
./scripts/deploy.sh rollback
```

---

## 📞 Context for Tomorrow

**Branch**: `feat/deployment-automation`  
**Next Milestone**: First successful deployment to localhost + RPi  
**Blockers**: GitHub PAT and MQTT password needed for vault creation  
**Risk**: Container images may not exist in GHCR yet  

**Questions to Answer Tomorrow**:

- Do we need to build Docker images before deploying?
- Is Docker already on the RPi or do we need to provision it?
- Should we test with staging inventory first (safer)?

---

*Generated: 2025-11-24 End of Day*  
*Branch: feat/deployment-automation*  
*Status: Ready for deployment testing*
