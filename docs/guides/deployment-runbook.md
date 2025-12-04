# Deployment Runbook

**Version:** 1.0  
**Last Updated:** 2025-11-24  
**Target Audience:** Operators, DevOps, Developers

---

## Table of Contents

- [Quick Start](#quick-start)
- [Prerequisites](#prerequisites)
- [Initial Setup](#initial-setup)
- [Deployment Workflows](#deployment-workflows)
- [Common Operations](#common-operations)
- [Troubleshooting](#troubleshooting)
- [Reference](#reference)

---

## Quick Start

### Deploy Everything (New Installation)

```bash
# 1. Set up secrets
cd infra/ansible
ansible-vault create secrets/vault.yml
# (Use template from secrets/vault.yml.example)

# 2. Update inventory
vi inventory/production/hosts.yml
# (Add your actual IPs and hostnames)

# 3. Provision RPi devices
./scripts/deploy.sh provision

# 4. Deploy central infrastructure
./scripts/deploy.sh central

# 5. Deploy edge controllers
./scripts/deploy.sh edge

# 6. Verify
./scripts/deploy.sh status
```

### Deploy Using Makefile

```bash
# Provision
make deploy-provision

# Deploy central
make deploy-central

# Deploy edge
make deploy-edge

# Check status
make deploy-status
```

---

## Prerequisites

### Control Machine (Your Laptop)

```bash
# Install Ansible
pip install ansible

# Install required Ansible collections
ansible-galaxy collection install community.docker
ansible-galaxy collection install community.general

# Verify installation
ansible --version
```

### Network Requirements

- SSH access to all hosts (central server + RPi devices)
- Static IP addresses or mDNS hostnames configured
- Firewall rules allowing:
  - SSH (22) from control machine to all hosts
  - MQTT (1883, 9001) from edge devices to central server
  - HTTP (8000) from edge devices to central server

### SSH Key Setup

```bash
# Generate SSH key if you don't have one
ssh-keygen -t ed25519 -C "train-control-deployment"

# Copy to central server
ssh-copy-id ubuntu@192.168.1.10

# Copy to each RPi
ssh-copy-id pi@192.168.1.101
ssh-copy-id pi@192.168.1.102
# ... etc

# Test passwordless SSH
ssh ubuntu@192.168.1.10 "echo 'SSH works'"
ssh pi@192.168.1.101 "echo 'SSH works'"
```

---

## Initial Setup

### Step 1: Configure Inventory

Edit `infra/ansible/inventory/production/hosts.yml`:

```yaml
central:
  hosts:
    train-server:
      ansible_host: 192.168.1.10  # YOUR SERVER IP
      ansible_user: ubuntu         # YOUR USERNAME

edge:
  hosts:
    rpi-train-01:
      ansible_host: 192.168.1.101  # YOUR RPI IP
      train_id: train-001
      train_name: "Express Line 1"
```

### Step 2: Create Vault with Secrets

```bash
cd infra/ansible

# Create encrypted vault
ansible-vault create secrets/vault.yml
# Enter vault password when prompted

# Add secrets (use template from vault.yml.example):
vault_github_username: your-github-username
vault_github_token: ghp_xxxxxxxxxxxxx
vault_mqtt_password: your-secure-password
```

### Step 3: Save Vault Password (Optional)

```bash
# Create password file
echo "your_vault_password" > ~/.ansible_vault_pass
chmod 600 ~/.ansible_vault_pass

# Export for scripts to use
export ANSIBLE_VAULT_PASSWORD_FILE=~/.ansible_vault_pass
```

---

## Deployment Workflows

### Workflow 1: Provision New Raspberry Pi

**When to use:** First-time setup of an RPi device

```bash
# Add to inventory first
vi infra/ansible/inventory/production/hosts.yml

# Provision the device
./scripts/deploy.sh provision rpi-train-01

# Or use Makefile
make deploy-provision HOST=rpi-train-01
```

**What it does:**

- Sets hostname
- Installs Docker
- Configures mDNS (Avahi)
- Adds user to docker group
- Creates directories
- Optimizes for SD card longevity

**Duration:** ~5-10 minutes per device

---

### Workflow 2: Deploy Central Infrastructure

**When to use:** Initial deployment or major updates to central components

```bash
./scripts/deploy.sh central

# Or
make deploy-central
```

**What it does:**

- Configures Mosquitto MQTT broker
- Deploys central_api container
- Sets up Docker Compose
- Creates health checks

**Expected Output:**

```
✅ Central infrastructure deployed successfully!

Services:
  MQTT Broker: 192.168.1.10:1883
  Central API: http://192.168.1.10:8000
  Health Check: http://192.168.1.10:8000/api/ping
```

**Verify:**

```bash
curl http://192.168.1.10:8000/api/ping
# Expected: {"status": "ok"}
```

---

### Workflow 3: Deploy Edge Controllers

**When to use:** Initial deployment or deploying to new devices

```bash
# Deploy to all edge devices
./scripts/deploy.sh edge

# Deploy to specific device
./scripts/deploy.sh edge rpi-train-01

# Or with Makefile
make deploy-edge HOST=rpi-train-01
```

**What it does:**

- Pulls edge-controller Docker image
- Creates configuration files
- Deploys container with GPIO access
- Sets up auto-restart
- Verifies connectivity to central API

**Expected Output:**

```
✅ Edge controller deployed successfully!

Device: rpi-train-01
Train ID: train-001
Container: edge-controller
MQTT Broker: 192.168.1.10:1883
Central API: http://192.168.1.10:8000
```

**Verify:**

```bash
# SSH to RPi
ssh pi@rpi-train-01

# Check container
docker ps | grep edge-controller

# Check logs
docker logs edge-controller
```

---

### Workflow 4: Update Deployments

**When to use:** Deploying new versions after code changes

```bash
# Update everything
./scripts/deploy.sh update all

# Update only central
./scripts/deploy.sh update central

# Update only edge controllers
./scripts/deploy.sh update edge

# Or with Makefile
make deploy-update COMPONENT=edge
```

**What it does:**

- Pulls latest Docker images
- Restarts services if images changed
- Verifies health after restart

---

### Workflow 5: Rollback

**When to use:** After a failed deployment or to revert to known-good version

```bash
# Rollback to specific version
./scripts/deploy.sh rollback v1.2.0

# Rollback to SHA
./scripts/deploy.sh rollback sha-abc123
```

**What it does:**

- Pulls specified image tag
- Stops current containers
- Deploys rollback version
- Verifies services started

---

## Common Operations

### Check Deployment Status

```bash
./scripts/deploy.sh status

# Or
make deploy-status
```

### View Container Logs

```bash
# Central API logs
ssh ubuntu@192.168.1.10
docker compose -f /opt/train-control/docker-compose.yml logs -f central_api

# Edge controller logs
ssh pi@rpi-train-01
docker logs -f edge-controller
```

### Restart Services

```bash
# Restart central infrastructure
ssh ubuntu@192.168.1.10
docker compose -f /opt/train-control/docker-compose.yml restart

# Restart specific edge controller
ssh pi@rpi-train-01
docker restart edge-controller
```

### Run Ad-Hoc Commands

```bash
cd infra/ansible

# Ping all hosts
ansible all -i inventory/production/hosts.yml -m ping

# Get disk usage on all RPi
ansible edge -i inventory/production/hosts.yml -a "df -h" --become

# Restart Docker on all hosts
ansible all -i inventory/production/hosts.yml -a "systemctl restart docker" --become
```

### Deploy to Staging Environment

```bash
# Use staging inventory
INVENTORY=staging ./scripts/deploy.sh central
INVENTORY=staging ./scripts/deploy.sh edge
```

---

## Troubleshooting

### Issue: "Ansible not found"

**Solution:**

```bash
pip install ansible
# Or
brew install ansible  # macOS
```

### Issue: "Permission denied (publickey)"

**Cause:** SSH keys not set up

**Solution:**

```bash
# Copy SSH key to host
ssh-copy-id pi@192.168.1.101

# Or specify key explicitly
ssh -i ~/.ssh/id_ed25519 pi@192.168.1.101
```

### Issue: "Vault password required"

**Solution:**

```bash
# Provide password file
export ANSIBLE_VAULT_PASSWORD_FILE=~/.ansible_vault_pass

# Or use --ask-vault-pass
ansible-playbook playbooks/deploy_central.yml --ask-vault-pass
```

### Issue: "Cannot connect to Docker daemon"

**Cause:** User not in docker group

**Solution:**

```bash
# SSH to host
ssh pi@rpi-train-01

# Log out and back in for group to take effect
exit
ssh pi@rpi-train-01

# Verify
docker ps
```

### Issue: "Container fails to start"

**Debug steps:**

```bash
# Check container logs
docker logs edge-controller

# Check Docker events
docker events

# Inspect container
docker inspect edge-controller

# Try running manually
docker run --rm -it edge-controller /bin/bash
```

### Issue: "MQTT connection refused"

**Check MQTT broker:**

```bash
ssh ubuntu@192.168.1.10

# Check if Mosquitto is running
docker ps | grep mosquitto

# Check Mosquitto logs
docker logs mosquitto

# Test MQTT connection
mosquitto_sub -h localhost -p 1883 -t 'trains/#' -u edge-controller -P <password>
```

### Issue: "Central API unreachable"

**Check API:**

```bash
ssh ubuntu@192.168.1.10

# Check if API is running
docker ps | grep central_api

# Check API logs
docker logs central_api

# Test API
curl http://localhost:8000/api/ping

# Check firewall
sudo ufw status
```

### Get Verbose Ansible Output

```bash
cd infra/ansible

# Run playbook with verbosity
ansible-playbook -i inventory/production/hosts.yml \
  playbooks/deploy_edge.yml \
  --ask-vault-pass \
  -vvv  # Triple verbose
```

---

## Reference

### File Locations on Deployed Hosts

#### Central Server

```
/opt/train-control/
├── docker-compose.yml
├── .env
├── mosquitto/
│   ├── mosquitto.conf
│   └── passwords
└── .deployed

/var/lib/train-control/
└── central_api.db

/var/log/train-control/
└── (logs)
```

#### Raspberry Pi

```
/opt/train-control/
├── config/
│   └── edge-controller.conf
├── logs/
│   └── edge-controller.log
└── .deployed

/var/lib/train-control/
└── (data)
```

### Environment Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `INVENTORY` | Inventory to use | `production`, `staging` |
| `ANSIBLE_VAULT_PASSWORD_FILE` | Path to vault password | `~/.ansible_vault_pass` |
| `HOST` | Limit deployment to host | `rpi-train-01` |
| `COMPONENT` | Component to update | `central`, `edge`, `all` |

### Ansible Commands Reference

```bash
# List inventory
ansible-inventory -i inventory/production/hosts.yml --list

# Ping specific group
ansible edge -i inventory/production/hosts.yml -m ping

# Run playbook in check mode (dry-run)
ansible-playbook playbooks/deploy_edge.yml --check

# Run specific tags
ansible-playbook playbooks/deploy_central.yml --tags mqtt

# Limit to specific host
ansible-playbook playbooks/deploy_edge.yml --limit rpi-train-01

# Run with extra vars
ansible-playbook playbooks/rollback.yml --extra-vars "version=v1.2.0"
```

### Docker Commands on Hosts

```bash
# View running containers
docker ps

# View all containers
docker ps -a

# View logs
docker logs -f <container_name>

# Restart container
docker restart <container_name>

# Remove container
docker stop <container_name>
docker rm <container_name>

# View images
docker images

# Remove old images
docker image prune -a
```

### Useful Debugging

```bash
# Check network connectivity
ansible all -i inventory/production/hosts.yml -m shell -a "ping -c 3 192.168.1.10"

# Check disk space
ansible all -i inventory/production/hosts.yml -a "df -h"

# Check memory usage
ansible all -i inventory/production/hosts.yml -a "free -h"

# Check Docker status
ansible all -i inventory/production/hosts.yml -a "systemctl status docker" --become

# Get system info
ansible all -i inventory/production/hosts.yml -m setup
```

---

## Emergency Procedures

### Complete Teardown

```bash
# Stop all containers on central
ssh ubuntu@192.168.1.10
docker compose -f /opt/train-control/docker-compose.yml down -v

# Stop all edge controllers
ansible edge -i inventory/production/hosts.yml \
  -a "docker stop edge-controller && docker rm edge-controller" \
  --become
```

### Fresh Deployment

```bash
# 1. Teardown
# (See above)

# 2. Re-deploy
./scripts/deploy.sh central
./scripts/deploy.sh edge

# 3. Verify
./scripts/deploy.sh status
```

---

## Next Steps

1. **Set up monitoring:** See `docs/observability.md` (Phase 2)
2. **Configure CI/CD:** Integrate deployment into GitHub Actions
3. **Scale out:** Add more edge devices to inventory
4. **Migrate secrets:** Move to HashiCorp Vault (Phase 2)

---

## Support

- **Documentation:** See `docs/` directory
- **Architecture:** See `docs/deployment-decisions.md`
- **Local Testing:** See `docs/local-github-actions.md`
- **Issues:** GitHub Issues
