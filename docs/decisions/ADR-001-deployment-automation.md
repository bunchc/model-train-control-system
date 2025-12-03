# ADR-001: Deployment Automation Strategy

**Status:** Accepted  
**Date:** 2025-11-24  
**Updated:** 2025-11-25  

## Context

The Model Train Control System requires automated deployment to:

- A central host (Mac/Linux) running the Central API and MQTT broker
- Multiple Raspberry Pi devices running edge controllers with motor hardware

We evaluated five deployment approaches and needed to make decisions about secrets management, container registry, networking, and logging.

## Decision

### Deployment Tool: Ansible

**Evaluated Options:**
| Approach | Score | Pros | Cons |
|----------|-------|------|------|
| Ansible | 122/140 | Agent-less, mature, great for mixed environments | YAML syntax |
| Docker Compose + Scripts | 98/140 | Simple, familiar | Manual orchestration |
| K3s (Kubernetes) | 85/140 | Cloud-native, powerful | Overkill for ~5 devices |
| Terraform + Ansible | 78/140 | Great for cloud | RPi not well supported |
| Balena | 72/140 | Purpose-built for IoT | Vendor lock-in |

**Selected:** Ansible (highest score) for best balance of simplicity, flexibility, and edge device support.

### Secrets Management: Ansible Vault

- **Phase 1 (Current):** Ansible Vault for encrypted secrets
- **Phase 2 (>20 devices):** Migrate to HashiCorp Vault

### Container Registry: GitHub Container Registry (GHCR)

- Integrated with GitHub repos
- Free for public packages
- Multi-arch support (AMD64 + ARM64)

### Network Strategy

- **Production:** Static IPs for reliability
- **Staging:** mDNS (`.local` hostnames) for flexibility

### Logging

- **Phase 1 (Current):** Docker logs + Ansible verbose mode
- **Phase 2:** Loki/Grafana stack for centralized logging

## Implementation

### Ansible Infrastructure (`infra/ansible/`)

**Playbooks:**

- `provision_pi.yml` - Initial RPi setup (Docker, I2C, mDNS)
- `deploy_central.yml` - Deploy Central API + Mosquitto MQTT
- `deploy_edge.yml` - Deploy single edge controller
- `deploy_edge_multi_motor.yml` - Deploy multiple motors per device
- `update.yml` - Update existing deployments
- `rollback.yml` - Rollback to previous versions

**Inventories:**

- `production/hosts.yml` - Production config with static IPs
- `staging/hosts.yml` - Staging config with mDNS

### Hardware Type System

Controllers use `hardware_type` to determine GPIO requirements:

- `dc_motor` - Waveshare DC Motor HAT (I2C)
- `stepper_hat` - Waveshare Stepper Motor HAT
- `simulator` - No hardware (testing)

## Consequences

### Positive

- Single toolchain for all deployment needs
- Agent-less (no software on target devices beyond SSH)
- Excellent community support and documentation
- Easy to extend with custom modules

### Negative

- Learning curve for YAML-based playbooks
- Slower than push-based tools for large fleets

## References

- Full research: `docs/deployment-research.md`
- Detailed decisions: `docs/deployment-decisions.md`
- Operational runbook: `docs/deployment-runbook.md`
