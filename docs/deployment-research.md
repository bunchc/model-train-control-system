# Deployment Automation Research

**Author:** AI Research  
**Date:** 2025-11-24  
**Branch:** `feat/deployment-automation`  
**Status:** Research & Decision Phase

---

## Executive Summary

This document evaluates deployment automation approaches for the Model Train Control System, a distributed edge computing application with the following requirements:

**Deployment Targets:**

- **Central Infrastructure** (Single Host): `central_api` + `mqtt` (Docker Compose)
- **Edge Devices** (Multiple RPi): `edge-controllers` (Docker on ARM)

**Key Constraints:**

- Distributed system with heterogeneous infrastructure (x86 server + ARM edge)
- Need for idempotent, repeatable deployments
- Testing/validation via AI agents (Copilot)
- Minimize operational overhead
- Support for offline edge device provisioning

---

## Table of Contents

1. [System Architecture Context](#system-architecture-context)
2. [Deployment Requirements Matrix](#deployment-requirements-matrix)
3. [Option 1: Ansible (Recommended)](#option-1-ansible-recommended)
4. [Option 2: Docker Compose + Custom Scripting](#option-2-docker-compose--custom-scripting)
5. [Option 3: Kubernetes (K3s)](#option-3-kubernetes-k3s)
6. [Option 4: Terraform + Configuration Management](#option-4-terraform--configuration-management)
7. [Option 5: Balena Cloud](#option-5-balena-cloud)
8. [Comparative Analysis](#comparative-analysis)
9. [Recommendation & Next Steps](#recommendation--next-steps)

---

## System Architecture Context

### Current State

```
┌─────────────────────────────────────┐
│  Central Host (x86_64)              │
│  ┌──────────────┐  ┌──────────────┐ │
│  │ central_api  │  │ mosquitto    │ │
│  │ (FastAPI)    │  │ (MQTT)       │ │
│  │ Port: 8000   │  │ Ports: 1883, │ │
│  │              │  │       9001   │ │
│  └──────────────┘  └──────────────┘ │
│          Docker Compose              │
└─────────────────────────────────────┘
                 │
                 │ MQTT over TCP/IP
                 │
      ┌──────────┴──────────┐
      │                     │
┌─────▼─────┐         ┌─────▼─────┐
│ RPi #1    │         │ RPi #2    │
│ (ARM64)   │   ...   │ (ARM64)   │
│ ┌───────┐ │         │ ┌───────┐ │
│ │ edge- │ │         │ │ edge- │ │
│ │ ctrl  │ │         │ │ ctrl  │ │
│ └───────┘ │         │ └───────┘ │
│  Docker   │         │  Docker   │
└───────────┘         └───────────┘
```

### Deployment Workflow Goals

1. **Central Deployment:** Single command to deploy `central_api` + `mqtt` to a target host
2. **Edge Deployment:** Single command to provision & deploy `edge-controllers` to N RPi devices
3. **Update Management:** Push updates to edge devices without manual SSH
4. **Rollback:** Quick rollback capability on failure
5. **Observability:** Health checks, logs aggregation
6. **Secrets Management:** MQTT credentials, API keys

---

## Deployment Requirements Matrix

| Requirement | Priority | Details |
|-------------|----------|---------|
| **Idempotency** | CRITICAL | Re-run deployments without side effects |
| **Multi-Architecture** | CRITICAL | x86_64 (central) + ARM64 (edge) |
| **Offline Edge Support** | HIGH | Edge devices may not have internet during provisioning |
| **Secrets Management** | HIGH | MQTT passwords, API keys, TLS certs |
| **Rollback** | HIGH | Revert to previous working state |
| **Testing Integration** | HIGH | Copilot can validate deployments programmatically |
| **Low Ops Burden** | MEDIUM | Minimize infrastructure to maintain |
| **Observability** | MEDIUM | Centralized logging, health monitoring |
| **GitOps Friendly** | MEDIUM | Declarative config in Git |

---

## Option 1: Ansible (Recommended)

### Overview

Ansible is an agentless automation tool using SSH for remote orchestration. It uses YAML playbooks to define infrastructure state.

### Architecture

```yaml
# Inventory Structure
inventory/
  ├── production
  │   ├── central_hosts      # x86_64 servers
  │   └── edge_devices       # Raspberry Pi fleet
  └── group_vars/
      ├── central.yml        # central_api + mqtt config
      └── edge.yml           # edge-controller config

# Playbook Structure
playbooks/
  ├── deploy_central.yml     # Deploy central_api + mqtt
  ├── deploy_edge.yml        # Deploy edge-controllers
  ├── update_edge.yml        # Update edge fleet
  └── rollback.yml           # Rollback to previous version
```

### Example Deployment Flow

```bash
# Deploy central infrastructure
ansible-playbook -i inventory/production playbooks/deploy_central.yml

# Deploy to specific edge device
ansible-playbook -i inventory/production playbooks/deploy_edge.yml \
  --limit rpi-train-01

# Deploy to all edge devices
ansible-playbook -i inventory/production playbooks/deploy_edge.yml

# Rollback edge device
ansible-playbook -i inventory/production playbooks/rollback.yml \
  --limit rpi-train-01 \
  --extra-vars "version=v1.2.0"
```

### Pros

✅ **Agentless:** No daemon on RPi, only SSH  
✅ **Idempotent:** Modules check state before applying changes  
✅ **Multi-Architecture:** Built-in support via inventory groups  
✅ **Secrets Management:** Ansible Vault for encrypted vars  
✅ **Rich Ecosystem:** Docker, systemd, apt modules out-of-the-box  
✅ **Testing Friendly:** `--check` mode for dry-runs, JSON output  
✅ **Copilot Integration:** Playbooks are YAML (LLM-friendly)  
✅ **GitOps:** Playbooks + inventory in version control  
✅ **Error Handling:** Built-in retry, rollback strategies  

### Cons

❌ **Learning Curve:** Ansible DSL and Jinja2 templating  
❌ **Performance:** SSH overhead (mitigated by `pipelining`)  
❌ **Offline Edge:** Requires network access during provisioning  

### Offline Edge Workaround

```yaml
# Pre-stage Docker images locally
- name: Copy Docker image to RPi
  copy:
    src: "{{ playbook_dir }}/../images/edge-controller-arm64.tar"
    dest: /tmp/edge-controller.tar

- name: Load Docker image
  docker_image:
    name: edge-controller
    load_path: /tmp/edge-controller.tar
    source: load
```

### Testing Integration (Copilot)

```python
# Copilot can execute Ansible and parse JSON output
import subprocess
import json

result = subprocess.run(
    ["ansible-playbook", "-i", "inventory/prod", "deploy_edge.yml",
     "--limit", "rpi-train-01", "--check", "-v"],
    capture_output=True, text=True
)

# Parse JSON output for validation
output = json.loads(result.stdout)
assert output['stats']['ok'] > 0
assert output['stats']['failures'] == 0
```

### Implementation Estimate

- **Setup Time:** 2-3 days (playbooks, inventory, secrets)
- **Learning Curve:** 1-2 days (if unfamiliar with Ansible)
- **Maintenance:** Low (declarative playbooks)

---

## Option 2: Docker Compose + Custom Scripting

### Overview

Extend existing `docker-compose.yml` with bash/Python scripts for deployment orchestration.

### Architecture

```
scripts/
  ├── deploy_central.sh      # SSH + docker-compose up
  ├── deploy_edge.sh         # Loop over RPi hosts, SSH + docker run
  ├── provision_pi.sh        # Install Docker, pull images
  └── inventory.txt          # List of RPi hostnames/IPs

infra/docker/
  ├── docker-compose.central.yml
  └── docker-compose.edge.yml
```

### Example Deployment

```bash
# scripts/deploy_central.sh
#!/bin/bash
CENTRAL_HOST="train-server.local"

ssh user@${CENTRAL_HOST} << 'EOF'
  cd /opt/train-control
  git pull
  docker-compose -f infra/docker/docker-compose.central.yml up -d
EOF
```

```bash
# scripts/deploy_edge.sh
#!/bin/bash
while IFS= read -r RPI_HOST; do
  echo "Deploying to ${RPI_HOST}..."
  ssh pi@${RPI_HOST} << 'EOF'
    docker pull ghcr.io/your-org/edge-controller:latest
    docker stop edge-controller || true
    docker rm edge-controller || true
    docker run -d --name edge-controller \
      --restart unless-stopped \
      -e MQTT_BROKER=train-server.local \
      ghcr.io/your-org/edge-controller:latest
EOF
done < scripts/inventory.txt
```

### Pros

✅ **Simplicity:** Leverages existing Compose files  
✅ **No New Tools:** Just bash + SSH  
✅ **Quick Start:** Minimal setup time  
✅ **Flexibility:** Easy to customize per environment  

### Cons

❌ **No Idempotency:** Scripts may fail on re-run  
❌ **No State Tracking:** Hard to know what's deployed where  
❌ **Error Handling:** Manual retry logic needed  
❌ **Secrets Management:** Hardcoded or environment vars  
❌ **Testing:** Difficult to validate without execution  
❌ **Rollback:** Manual Docker tag management  

### When to Use

- **MVP/Prototype:** Quick deployment for testing
- **Small Scale:** <5 edge devices
- **Single Operator:** Not for team environments

---

## Option 3: Kubernetes (K3s)

### Overview

Lightweight Kubernetes distribution for edge computing. K3s runs on RPi and provides declarative deployment.

### Architecture

```
┌─────────────────────────────────────┐
│  Central Host (K3s Server)          │
│  ┌──────────────┐  ┌──────────────┐ │
│  │ central_api  │  │ mosquitto    │ │
│  │ (Deployment) │  │ (StatefulSet)│ │
│  └──────────────┘  └──────────────┘ │
└─────────────────────────────────────┘
                 │
      ┌──────────┴──────────┐
      │                     │
┌─────▼─────┐         ┌─────▼─────┐
│ RPi #1    │         │ RPi #2    │
│ (K3s Node)│         │ (K3s Node)│
│ ┌───────┐ │         │ ┌───────┐ │
│ │ edge- │ │         │ │ edge- │ │
│ │ ctrl  │ │         │ │ ctrl  │ │
│ │ (Pod) │ │         │ │ (Pod) │ │
│ └───────┘ │         │ └───────┘ │
└───────────┘         └───────────┘
```

### Example Deployment

```bash
# Install K3s on central host
curl -sfL https://get.k3s.io | sh -

# Install K3s agent on RPi
curl -sfL https://get.k3s.io | K3S_URL=https://central:6443 \
  K3S_TOKEN=<token> sh -

# Deploy manifests
kubectl apply -f infra/k8s/manifests/
```

### Pros

✅ **Declarative:** GitOps-native (Flux, ArgoCD)  
✅ **Self-Healing:** Auto-restart failed containers  
✅ **Observability:** Built-in metrics, logging  
✅ **Rollback:** `kubectl rollout undo`  
✅ **Secrets Management:** Native Secret resources  
✅ **Service Discovery:** DNS-based service mesh  

### Cons

❌ **Complexity:** Kubernetes learning curve is steep  
❌ **Resource Overhead:** K3s requires 512MB+ RAM per node  
❌ **Network Dependency:** Requires persistent connection to control plane  
❌ **Hardware Access:** GPIO/I2C requires privileged pods + node affinity  
❌ **Offline Edge:** Not suitable (agents need control plane)  
❌ **Overkill:** Too much for <10 edge devices  

### When to Use

- **Scale:** >20 edge devices
- **Cloud-Native Team:** Already familiar with K8s
- **Future-Proofing:** Plan to add ML inference, observability stack

### Hardware Access Challenge

```yaml
# edge-controller deployment needs GPIO access
apiVersion: apps/v1
kind: DaemonSet  # One pod per RPi
metadata:
  name: edge-controller
spec:
  template:
    spec:
      hostNetwork: true
      hostPID: true
      containers:
      - name: controller
        image: edge-controller:latest
        securityContext:
          privileged: true  # Required for GPIO
        volumeMounts:
        - name: dev
          mountPath: /dev
        - name: sys
          mountPath: /sys
      volumes:
      - name: dev
        hostPath:
          path: /dev
      - name: sys
        hostPath:
          path: /sys
```

---

## Option 4: Terraform + Configuration Management

### Overview

Use Terraform for infrastructure provisioning + Ansible/Packer for configuration.

### Architecture

```
infra/terraform/
  ├── main.tf               # VM provisioning (if cloud)
  ├── docker.tf             # Docker resources
  └── modules/
      ├── central/
      └── edge/

# Then use Ansible for app deployment (see Option 1)
```

### Pros

✅ **Infrastructure as Code:** Declarative VM/network setup  
✅ **State Management:** Terraform state tracks infra changes  
✅ **Multi-Cloud:** Portable across providers  

### Cons

❌ **Limited for Bare Metal:** Terraform shines with cloud APIs  
❌ **Two Tools:** Need Terraform + Ansible/Packer  
❌ **Complexity:** Overhead for small deployments  

### When to Use

- **Cloud Deployment:** Provisioning VMs on AWS/Azure/GCP
- **Hybrid Cloud:** Managing both cloud + on-prem resources
- **Not Recommended for This Project:** RPi are pre-existing hardware

---

## Option 5: Balena Cloud

### Overview

IoT fleet management platform specifically designed for edge devices. Provides OTA updates, remote access, and monitoring.

### Architecture

```
Balena Cloud (SaaS)
       │
       │ (Balena VPN)
       │
  ┌────┴────┐
  │         │
RPi #1    RPi #2
(balenaOS) (balenaOS)
```

### How It Works

1. Flash RPi with balenaOS (custom Linux distro)
2. RPi phones home to Balena Cloud
3. Deploy via `balena push` (Docker Compose-based)
4. OTA updates, remote SSH, logs dashboard

### Pros

✅ **IoT-Optimized:** Built for Raspberry Pi fleet management  
✅ **OTA Updates:** Push updates to all devices remotely  
✅ **Remote Access:** SSH into devices behind NAT  
✅ **Observability:** Centralized logs, metrics dashboard  
✅ **Rollback:** One-click rollback to previous release  
✅ **Offline Resilient:** Devices cache updates and apply when online  

### Cons

❌ **SaaS Dependency:** Relies on Balena Cloud availability  
❌ **Cost:** Free tier: 10 devices. Paid plans: $20/device/month  
❌ **Vendor Lock-In:** balenaOS is proprietary  
❌ **Learning Curve:** Balena-specific tooling (`balena-cli`)  
❌ **Central API Deployment:** Doesn't help with central host deployment  

### When to Use

- **Fleet Management:** >10 RPi devices in production
- **Remote Sites:** Devices in hard-to-reach locations
- **Budget Available:** Can afford SaaS costs
- **Not Recommended for This Project:** You need a solution for both central + edge

---

## Comparative Analysis

### Feature Matrix

| Feature | Ansible | Docker Compose + Scripts | K3s | Terraform + CM | Balena Cloud |
|---------|---------|--------------------------|-----|----------------|--------------|
| **Idempotency** | ✅ Excellent | ❌ Poor | ✅ Excellent | ✅ Good | ✅ Excellent |
| **Multi-Arch Support** | ✅ Native | ✅ Manual | ✅ Native | ✅ Native | ✅ Native |
| **Offline Edge** | ⚠️ Workaround | ✅ Yes | ❌ No | ⚠️ Partial | ⚠️ Eventual |
| **Secrets Mgmt** | ✅ Ansible Vault | ❌ Manual | ✅ Native | ✅ Good | ✅ Native |
| **Rollback** | ✅ Built-in | ❌ Manual | ✅ Automatic | ✅ Good | ✅ One-Click |
| **Testing (Copilot)** | ✅ JSON output | ⚠️ Custom | ✅ `kubectl` | ✅ `terraform plan` | ⚠️ API-based |
| **Learning Curve** | ⚠️ Medium | ✅ Low | ❌ High | ❌ High | ⚠️ Medium |
| **Ops Burden** | ✅ Low | ⚠️ Medium | ❌ High | ⚠️ Medium | ✅ Low (SaaS) |
| **GitOps** | ✅ Excellent | ⚠️ Manual | ✅ Excellent | ✅ Excellent | ✅ Good |
| **Cost** | ✅ Free (OSS) | ✅ Free | ✅ Free (OSS) | ✅ Free (OSS) | ❌ Paid ($$$) |
| **Edge Scale** | ✅ 1-100+ | ⚠️ 1-10 | ✅ 10-1000+ | ✅ 10-100+ | ✅ 10-10000+ |
| **GPIO/Hardware** | ✅ Full control | ✅ Full control | ⚠️ Requires config | ✅ Full control | ✅ Full control |

### Scoring (Out of 10)

| Criteria | Weight | Ansible | Scripts | K3s | Terraform | Balena |
|----------|--------|---------|---------|-----|-----------|--------|
| **Ease of Use** | 3x | 7 | 9 | 4 | 5 | 8 |
| **Scalability** | 2x | 8 | 4 | 10 | 8 | 10 |
| **Maintenance** | 3x | 9 | 5 | 6 | 7 | 9 |
| **Testing** | 2x | 9 | 5 | 8 | 8 | 7 |
| **Cost** | 1x | 10 | 10 | 10 | 10 | 3 |
| **Fit for Project** | 3x | 9 | 6 | 5 | 6 | 6 |
| **Weighted Total** | | **122** | **89** | **94** | **99** | **105** |

---

## Recommendation & Next Steps

### Recommended Approach: **Ansible + Docker**

**Rationale:**

1. **Best Overall Fit:** Balances ease of use, scalability, and operational simplicity
2. **Copilot-Friendly:** YAML playbooks are LLM-readable and testable
3. **Idempotent:** Safe to re-run deployments
4. **Multi-Architecture:** Handles x86_64 central + ARM64 edge natively
5. **GitOps:** Playbooks + inventory in version control
6. **Low Cost:** No SaaS fees, only infrastructure costs
7. **Proven:** Ansible is industry-standard for hybrid cloud/edge deployments

### Hybrid Consideration

For **future scale** (>50 RPi devices), consider:

- **Ansible for Provisioning** (OS setup, Docker install)
- **Balena Cloud for Fleet Management** (OTA updates, monitoring)

But for current scope (<10 devices), pure Ansible is optimal.

---

## Proposed Implementation Roadmap

### Phase 1: Foundation (Week 1)

- [ ] Install Ansible on control machine (your dev laptop)
- [ ] Create `infra/ansible/` directory structure
- [ ] Define inventory for 1 central host + 1 test RPi
- [ ] Create basic playbook for central deployment (`central_api` + `mqtt`)
- [ ] Test central deployment to dev environment
- [ ] Document workflow in `docs/deployment.md`

### Phase 2: Edge Deployment (Week 2)

- [ ] Create edge controller playbook
- [ ] Add Docker image pre-loading for offline scenarios
- [ ] Implement secrets management with Ansible Vault
- [ ] Test edge deployment to 1 RPi
- [ ] Create update + rollback playbooks

### Phase 3: Observability (Week 3)

- [ ] Add health checks to playbooks
- [ ] Implement log aggregation (optional: Loki stack)
- [ ] Create monitoring dashboard (optional: Grafana)
- [ ] Document troubleshooting procedures

### Phase 4: CI/CD Integration (Week 4)

- [ ] Add GitHub Actions workflow to lint playbooks
- [ ] Create `ansible-playbook --check` pre-deployment validation
- [ ] Implement versioned deployments (Git tags → Docker tags)
- [ ] Test Copilot-driven deployment validation

---

## File Structure Preview

```
model-train-control-system/
├── infra/
│   ├── ansible/
│   │   ├── ansible.cfg                 # Ansible configuration
│   │   ├── inventory/
│   │   │   ├── production/
│   │   │   │   ├── hosts.yml           # central + edge hosts
│   │   │   │   └── group_vars/
│   │   │   │       ├── central.yml     # central config vars
│   │   │   │       └── edge.yml        # edge config vars
│   │   │   └── staging/
│   │   │       └── hosts.yml
│   │   ├── playbooks/
│   │   │   ├── deploy_central.yml      # Deploy central_api + mqtt
│   │   │   ├── deploy_edge.yml         # Deploy edge-controllers
│   │   │   ├── provision_pi.yml        # Initial RPi setup
│   │   │   ├── update_edge.yml         # Update edge fleet
│   │   │   └── rollback.yml            # Rollback deployments
│   │   ├── roles/
│   │   │   ├── docker/                 # Install Docker on hosts
│   │   │   ├── central_api/            # central_api deployment
│   │   │   ├── mqtt/                   # Mosquitto deployment
│   │   │   └── edge_controller/        # edge-controller deployment
│   │   └── secrets/
│   │       └── vault.yml               # Encrypted secrets (Ansible Vault)
│   └── docker/
│       └── docker-compose.yml          # (keep for local dev)
├── docs/
│   ├── deployment.md                   # Deployment runbook
│   └── deployment-research.md          # This document
└── scripts/
    └── deploy.sh                       # Wrapper for ansible-playbook
```

---

## Alternative: Quick Win with Enhanced Scripting

If Ansible is too heavy for immediate needs, enhance existing scripts:

### Minimal Viable Deployment (MVD)

```bash
# scripts/deploy.sh
#!/bin/bash
set -euo pipefail

COMPONENT="${1:-}"
TARGET="${2:-}"

case "$COMPONENT" in
  central)
    ssh user@"${TARGET}" << 'EOF'
      cd /opt/train-control
      docker-compose -f infra/docker/docker-compose.yml pull
      docker-compose -f infra/docker/docker-compose.yml up -d central_api mqtt
EOF
    ;;
  edge)
    # Loop over inventory
    while IFS= read -r RPI_HOST; do
      ssh pi@"${RPI_HOST}" << 'EOF'
        docker pull ghcr.io/your-org/edge-controller:latest
        docker stop edge-controller || true
        docker rm edge-controller || true
        docker run -d --name edge-controller \
          --restart unless-stopped \
          --privileged \
          -v /dev:/dev \
          -e MQTT_BROKER="${MQTT_BROKER}" \
          ghcr.io/your-org/edge-controller:latest
EOF
    done < scripts/edge_inventory.txt
    ;;
  *)
    echo "Usage: $0 {central|edge} <target>"
    exit 1
    ;;
esac
```

**Pros:** Works immediately, no new tools  
**Cons:** Not idempotent, limited error handling, harder to test

---

## Key Takeaways

### For Your Use Case (Central + Edge Deployment)

1. **Ansible is the sweet spot** for your scale and requirements
2. **Docker Compose + Scripts** is acceptable for MVP but doesn't scale
3. **K3s is overkill** unless you're planning >20 devices or need service mesh
4. **Balena Cloud** is excellent for edge-only, but doesn't solve central deployment
5. **Terraform** doesn't add value for bare-metal RPi deployments

### Decision Drivers

- **If learning time is limited:** Start with enhanced scripts, migrate to Ansible later
- **If long-term maintainability matters:** Go directly to Ansible
- **If you need remote fleet management:** Consider Balena Cloud for edge (Ansible for central)
- **If you're planning Kubernetes expertise:** K3s is a learning investment, not immediate ROI

---

## Questions for Next Phase

Before implementation, clarify:

1. **Inventory:** Do you have fixed IP addresses for RPi devices? Or DNS names?
2. **Secrets:** Where will you store MQTT passwords? (Ansible Vault? External KMS?)
3. **Image Registry:** GitHub Container Registry? Docker Hub? Private registry?
4. **Offline Requirement:** How often are RPi devices offline? (Determines caching strategy)
5. **Monitoring:** Do you need centralized logs/metrics now or later?
6. **CI/CD:** Should deployment be automated on Git push, or manual trigger?

---

## References

- [Ansible Documentation](https://docs.ansible.com/)
- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [K3s Documentation](https://k3s.io/)
- [Balena Documentation](https://www.balena.io/docs/)
- [Ansible for IoT Edge Deployment](https://www.ansible.com/use-cases/edge-computing)
- [Raspberry Pi Fleet Management Best Practices](https://www.raspberrypi.com/documentation/computers/remote-access.html)

---

**Next Action:** Review this document with the team and decide on:

1. Ansible (recommended) vs. Enhanced Scripts (quick win)
2. Timeline for implementation (immediate vs. phased)
3. Answers to clarification questions above

Then proceed to implementation phase in this feature branch.
