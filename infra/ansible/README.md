# Ansible Deployment Infrastructure

This directory contains Ansible playbooks and configuration for deploying the Model Train Control System to distributed edge devices.

## Quick Start

```bash
# 1. Set up secrets
ansible-vault create secrets/vault.yml

# 2. Update inventory
vi inventory/production/hosts.yml

# 3. Run deployments
../../scripts/deploy.sh provision    # Provision RPi devices
../../scripts/deploy.sh central      # Deploy central infrastructure
../../scripts/deploy.sh edge         # Deploy edge controllers
```

## Directory Structure

```
infra/ansible/
├── ansible.cfg                 # Ansible configuration
├── playbooks/                  # Deployment playbooks
│   ├── provision_pi.yml       # Provision Raspberry Pi devices
│   ├── deploy_central.yml     # Deploy central_api + mqtt
│   ├── deploy_edge.yml        # Deploy edge-controllers
│   ├── update.yml             # Update existing deployments
│   └── rollback.yml           # Rollback to previous version
├── inventory/                  # Host inventories
│   ├── production/
│   │   └── hosts.yml          # Production hosts
│   └── staging/
│       └── hosts.yml          # Staging/dev hosts
├── roles/                      # Reusable Ansible roles (future)
└── secrets/                    # Encrypted secrets (Ansible Vault)
    ├── vault.yml.example      # Template for secrets
    └── vault.yml              # Actual secrets (encrypted, not in Git)
```

## Prerequisites

### Install Ansible

```bash
pip install ansible

# Install required collections
ansible-galaxy collection install community.docker
ansible-galaxy collection install community.general
```

### Set Up SSH Keys

```bash
# Copy SSH key to all hosts
ssh-copy-id ubuntu@central-server
ssh-copy-id pi@rpi-train-01
ssh-copy-id pi@rpi-train-02
```

## Configuration

### 1. Create Secrets Vault

```bash
# Create encrypted vault
ansible-vault create secrets/vault.yml

# Use template from vault.yml.example
# Add:
# - GitHub token for container registry
# - MQTT password
# - Other secrets
```

### 2. Update Inventory

Edit `inventory/production/hosts.yml`:

- Replace example IPs with your actual IPs
- Update usernames if different
- Add/remove edge devices as needed
- Configure train IDs and names

### 3. Configure Ansible

The `ansible.cfg` file is pre-configured with sensible defaults:

- SSH connection optimization
- Privilege escalation settings
- Logging configuration

Modify if needed for your environment.

## Usage

### Using Wrapper Script (Recommended)

```bash
# From project root
./scripts/deploy.sh provision        # Provision RPi
./scripts/deploy.sh central          # Deploy central
./scripts/deploy.sh edge             # Deploy edge
./scripts/deploy.sh status           # Check status
./scripts/deploy.sh update all       # Update all
./scripts/deploy.sh rollback v1.2.0  # Rollback

# Target specific host
./scripts/deploy.sh provision rpi-train-01
./scripts/deploy.sh edge rpi-train-01

# Use staging inventory
INVENTORY=staging ./scripts/deploy.sh edge
```

### Using Ansible Directly

```bash
cd infra/ansible

# Provision RPi devices
ansible-playbook -i inventory/production/hosts.yml \
  playbooks/provision_pi.yml \
  --ask-vault-pass

# Deploy central infrastructure
ansible-playbook -i inventory/production/hosts.yml \
  playbooks/deploy_central.yml \
  --ask-vault-pass

# Deploy edge controllers
ansible-playbook -i inventory/production/hosts.yml \
  playbooks/deploy_edge.yml \
  --ask-vault-pass

# Limit to specific host
ansible-playbook -i inventory/production/hosts.yml \
  playbooks/deploy_edge.yml \
  --limit rpi-train-01 \
  --ask-vault-pass

# Dry-run (check mode)
ansible-playbook -i inventory/production/hosts.yml \
  playbooks/deploy_edge.yml \
  --check
```

### Using Makefile

```bash
# From project root
make deploy-provision           # Provision all RPi
make deploy-central             # Deploy central
make deploy-edge                # Deploy all edge
make deploy-status              # Check status

# Target specific host
make deploy-edge HOST=rpi-train-01

# Update specific component
make deploy-update COMPONENT=edge
```

## Playbooks

### provision_pi.yml

**Purpose:** Initial setup of Raspberry Pi devices

**What it does:**

- Sets hostname
- Installs Docker
- Configures mDNS (Avahi)
- Adds user to docker group
- Creates directories
- Optimizes for SD card

**When to run:** Once per new RPi device

```bash
ansible-playbook playbooks/provision_pi.yml --limit rpi-train-01
```

### deploy_central.yml

**Purpose:** Deploy central infrastructure (API + MQTT)

**What it does:**

- Configures Mosquitto MQTT broker
- Deploys central_api container via Docker Compose
- Sets up health checks
- Creates configuration files

**When to run:** Initial deployment or major updates

```bash
ansible-playbook playbooks/deploy_central.yml
```

### deploy_edge.yml

**Purpose:** Deploy edge controllers to RPi devices

**What it does:**

- Pulls edge-controller Docker image
- Creates configuration files
- Deploys container with GPIO access
- Verifies connectivity

**When to run:** Initial deployment or when adding new devices

```bash
ansible-playbook playbooks/deploy_edge.yml
```

### update.yml

**Purpose:** Update deployed services to latest versions

**What it does:**

- Pulls latest Docker images
- Restarts services if images changed
- Verifies health

**When to run:** After pushing new code

```bash
ansible-playbook playbooks/update.yml
ansible-playbook playbooks/update.yml --tags central
ansible-playbook playbooks/update.yml --tags edge
```

### rollback.yml

**Purpose:** Rollback to previous version

**What it does:**

- Pulls specified image tag
- Stops current containers
- Deploys rollback version

**When to run:** After failed deployment

```bash
ansible-playbook playbooks/rollback.yml --extra-vars "version=v1.2.0"
```

## Inventory Management

### Production Inventory

Located at `inventory/production/hosts.yml`

**Central hosts:**

- x86_64 servers running central_api + mqtt

**Edge hosts:**

- Raspberry Pi devices running edge-controllers

Example:

```yaml
central:
  hosts:
    train-server:
      ansible_host: 192.168.1.10
      ansible_user: ubuntu

edge:
  hosts:
    rpi-train-01:
      ansible_host: 192.168.1.101
      ansible_user: pi
      train_id: train-001
```

### Staging Inventory

Located at `inventory/staging/hosts.yml`

Uses mDNS (`.local`) hostnames for easier development:

```yaml
central:
  hosts:
    train-server:
      ansible_host: train-server.local

edge:
  hosts:
    rpi-train-01:
      ansible_host: rpi-train-01.local
```

## Secrets Management

### Ansible Vault

Secrets are encrypted using Ansible Vault.

**Create vault:**

```bash
ansible-vault create secrets/vault.yml
```

**Edit vault:**

```bash
ansible-vault edit secrets/vault.yml
```

**View vault:**

```bash
ansible-vault view secrets/vault.yml
```

**Use vault in playbooks:**

```bash
# Prompted for password
ansible-playbook playbooks/deploy.yml --ask-vault-pass

# Use password file
ansible-playbook playbooks/deploy.yml \
  --vault-password-file ~/.ansible_vault_pass
```

### Required Secrets

```yaml
vault_github_username: your-github-username
vault_github_token: ghp_xxxxxxxxxxxxx
vault_mqtt_password: your-secure-password
```

## Common Tasks

### Check Connectivity

```bash
ansible all -i inventory/production/hosts.yml -m ping
```

### Get Facts

```bash
ansible edge -i inventory/production/hosts.yml -m setup
```

### Run Ad-Hoc Commands

```bash
# Check disk usage
ansible all -i inventory/production/hosts.yml -a "df -h"

# Check Docker status
ansible all -i inventory/production/hosts.yml \
  -a "systemctl status docker" --become

# View running containers
ansible all -i inventory/production/hosts.yml \
  -a "docker ps" --become
```

### Debug Playbooks

```bash
# Verbose output
ansible-playbook playbooks/deploy_edge.yml -vvv

# Dry-run (check mode)
ansible-playbook playbooks/deploy_edge.yml --check

# Step-by-step execution
ansible-playbook playbooks/deploy_edge.yml --step
```

## Troubleshooting

### Connection Issues

```bash
# Test SSH
ssh pi@192.168.1.101

# Check SSH config
cat ~/.ssh/config

# Verify SSH key
ssh-add -L
```

### Vault Issues

```bash
# Reset vault password
ansible-vault rekey secrets/vault.yml

# Verify vault syntax
ansible-vault view secrets/vault.yml
```

### Playbook Failures

```bash
# Run with maximum verbosity
ansible-playbook playbooks/deploy_edge.yml -vvvv

# Check logs on remote host
ssh pi@rpi-train-01
journalctl -xe
docker logs edge-controller
```

## Best Practices

1. **Always use check mode first:** `--check` to see what would change
2. **Limit deployments:** Use `--limit` for specific hosts during testing
3. **Keep vault password safe:** Use password manager, never commit
4. **Test in staging:** Deploy to staging before production
5. **Use tags:** Deploy specific components with `--tags`
6. **Version control:** Commit inventory and playbook changes
7. **Document changes:** Update this README when making changes

## Integration with CI/CD

### GitHub Actions

```yaml
- name: Deploy to edge devices
  run: |
    echo "${{ secrets.ANSIBLE_VAULT_PASSWORD }}" > .vault_pass
    export ANSIBLE_VAULT_PASSWORD_FILE=.vault_pass
    ./scripts/deploy.sh edge
```

### Manual Deployment

Always test locally before automating:

```bash
# Test in staging
INVENTORY=staging ./scripts/deploy.sh edge

# Deploy to production
./scripts/deploy.sh edge
```

## Further Reading

- [Deployment Runbook](../../docs/deployment-runbook.md) - Complete deployment guide
- [Deployment Decisions](../../docs/deployment-decisions.md) - Architecture decisions
- [Ansible Documentation](https://docs.ansible.com/)
- [Docker Ansible Collection](https://docs.ansible.com/ansible/latest/collections/community/docker/)

## Support

For issues or questions:

1. Check [deployment-runbook.md](../../docs/deployment-runbook.md) troubleshooting section
2. Run playbooks with `-vvv` for detailed output
3. Open GitHub issue with error details
