# Deployment Architecture Decisions

**Date:** 2025-11-24  
**Branch:** `feat/deployment-automation`  
**Status:** Decision Phase → Implementation Ready

---

## Executive Summary

Based on clarifications, we're implementing **Ansible-based deployment** with the following supporting infrastructure:

| Component | Solution | Rationale |
|-----------|----------|-----------|
| **Orchestration** | Ansible | Idempotent, testable, GitOps-friendly |
| **Secrets Management** | Ansible Vault + HashiCorp Vault (optional) | Local-first, deployable, secure |
| **Container Registry** | GitHub Container Registry (GHCR) | Free, integrated with repo, no self-hosting |
| **Network Topology** | Static IPs + mDNS (Avahi) | Dual approach: reliable + discoverable |
| **Logging** | Defer to Phase 2 | Can troubleshoot via Ansible verbose mode initially |

---

## 1. Secrets Management Solution

### Requirement
>
> "What is a local thing we can run for this? It should also be a deployable component."

### Recommended Approach: **Tiered Strategy**

#### Tier 1 (Immediate): Ansible Vault

**What it is:** Built-in encryption for Ansible variables

```yaml
# infra/ansible/secrets/vault.yml (encrypted)
---
mqtt_password: "super_secret_password_123"
api_key: "your-api-key-here"
central_api_db_password: "db_password_456"
```

**How to use:**

```bash
# Create encrypted vault
ansible-vault create infra/ansible/secrets/vault.yml

# Edit vault
ansible-vault edit infra/ansible/secrets/vault.yml

# Run playbook with vault
ansible-playbook -i inventory/production deploy_central.yml \
  --ask-vault-pass
```

**Pros:**
✅ No additional infrastructure needed  
✅ Encrypted at rest in Git  
✅ Works out-of-the-box with Ansible  
✅ Can use password files or system keychain  

**Cons:**
❌ Not a centralized secrets server  
❌ Requires password/key to decrypt  
❌ Can't rotate secrets without re-encrypting  

**Verdict:** ✅ **START HERE** - Sufficient for initial deployment

---

#### Tier 2 (Future - Optional): HashiCorp Vault

**What it is:** Centralized secrets management server

**Deployment:**

```yaml
# Add to docker-compose.yml on central host
services:
  vault:
    image: hashicorp/vault:latest
    ports:
      - "8200:8200"
    environment:
      VAULT_DEV_ROOT_TOKEN_ID: "root"  # DEV ONLY
      VAULT_DEV_LISTEN_ADDRESS: "0.0.0.0:8200"
    volumes:
      - vault_data:/vault/data
    cap_add:
      - IPC_LOCK
```

**Ansible Integration:**

```yaml
# playbooks/deploy_edge.yml
- name: Get MQTT password from Vault
  hashivault_read:
    secret: "mqtt/password"
    key: "value"
  register: mqtt_secret

- name: Deploy edge controller
  docker_container:
    name: edge-controller
    env:
      MQTT_PASSWORD: "{{ mqtt_secret.value }}"
```

**Pros:**
✅ Dynamic secrets with TTLs  
✅ Audit logging  
✅ Secret rotation without redeployment  
✅ API-driven (Copilot can validate)  

**Cons:**
❌ Requires running Vault server  
❌ Additional operational complexity  
❌ Overkill for <10 devices  

**Verdict:** ⚠️ **DEFER TO PHASE 2** - Migrate when you have >20 RPi devices or compliance requirements

---

### Decision: **Ansible Vault (Now) → Vault (Later)**

**Implementation Plan:**

1. Use Ansible Vault for MQTT passwords, API keys
2. Store vault password in CI/CD secrets (GitHub Actions)
3. Document migration path to HashiCorp Vault in runbook

---

## 2. Container Registry Solution

### Requirement
>
> "Which is straightforward and can be made part of the deployment bits?"

### Recommended: **GitHub Container Registry (GHCR)**

**Why GHCR over self-hosted?**

| Option | Setup Time | Cost | Maintenance | CI/CD Integration |
|--------|------------|------|-------------|-------------------|
| **GHCR** | 5 min | Free | None | Native GitHub Actions |
| Harbor (self-hosted) | 2-3 hours | $0 (compute) | Medium | Manual webhooks |
| Local Registry | 30 min | $0 | Low | Manual push |
| Docker Hub | 5 min | Free (public) | None | Good |

**GHCR Advantages:**
✅ **No infrastructure to maintain** (SaaS)  
✅ **Free for public repos** (unlimited bandwidth)  
✅ **Free for private repos** (500MB storage)  
✅ **GitHub Actions native** (automatic auth)  
✅ **Multi-arch builds** (x86_64 + ARM64)  
✅ **Scoped to repository** (no global namespace conflicts)  

---

### Implementation: GitHub Container Registry

#### Step 1: Build & Push Images (GitHub Actions)

```yaml
# .github/workflows/build-images.yml
name: Build and Push Docker Images

on:
  push:
    branches: [main, feat/*]
    tags: ['v*']

jobs:
  build-central-api:
    runs-on: ubuntu-latest
    permissions:
      contents: read
      packages: write
    steps:
      - uses: actions/checkout@v4

      - name: Log in to GHCR
        uses: docker/login-action@v3
        with:
          registry: ghcr.io
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}

      - name: Build and push
        uses: docker/build-push-action@v5
        with:
          context: ./central_api
          push: true
          tags: |
            ghcr.io/${{ github.repository }}/central-api:latest
            ghcr.io/${{ github.repository }}/central-api:${{ github.sha }}

  build-edge-controller:
    runs-on: ubuntu-latest
    permissions:
      contents: read
      packages: write
    steps:
      - uses: actions/checkout@v4

      - name: Set up QEMU (for ARM builds)
        uses: docker/setup-qemu-action@v3

      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v3

      - name: Log in to GHCR
        uses: docker/login-action@v3
        with:
          registry: ghcr.io
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}

      - name: Build and push (multi-arch)
        uses: docker/build-push-action@v5
        with:
          context: ./edge-controllers/pi-template
          platforms: linux/amd64,linux/arm64
          push: true
          tags: |
            ghcr.io/${{ github.repository }}/edge-controller:latest
            ghcr.io/${{ github.repository }}/edge-controller:${{ github.sha }}
```

#### Step 2: Pull from GHCR in Ansible

```yaml
# playbooks/deploy_edge.yml
- name: Log in to GHCR
  docker_login:
    registry: ghcr.io
    username: "{{ github_username }}"
    password: "{{ github_token }}"  # From Ansible Vault

- name: Pull edge controller image
  docker_image:
    name: "ghcr.io/bunchc/model-train-control-system/edge-controller"
    tag: latest
    source: pull
```

#### Step 3: Make Images Public (Optional)

```bash
# Run once to make images publicly accessible (no auth needed)
gh api \
  --method PUT \
  -H "Accept: application/vnd.github+json" \
  /user/packages/container/model-train-control-system%2Fedge-controller/visibility \
  -f visibility=public
```

**If public:** RPi can pull without credentials  
**If private:** Store GitHub token in Ansible Vault

---

### Alternative: Self-Hosted Registry (If Needed Later)

```yaml
# infra/docker/docker-compose.yml
services:
  registry:
    image: registry:2
    ports:
      - "5000:5000"
    volumes:
      - registry_data:/var/lib/registry
    environment:
      REGISTRY_STORAGE_DELETE_ENABLED: "true"

volumes:
  registry_data:
```

**When to use:**

- Air-gapped environments (no internet on RPi)
- Very large images (>1GB)
- Want complete control

**Verdict:** ⚠️ **DEFER** - GHCR is simpler for now

---

### Decision: **GitHub Container Registry (GHCR)**

**Why:**

- No infrastructure to maintain
- Free for this use case
- Multi-arch builds built-in
- GitHub Actions integration is seamless

---

## 3. Network Topology for RPi Devices

### Requirement
>
> "Not yet, but we can set that up as part of the deployment."

### Recommended: **Dual Strategy (Static IPs + mDNS)**

#### Approach 1: Static IP Reservation (DHCP)

**Best for:** Production reliability

```
Router DHCP Reservations:
┌─────────────────┬──────────────────┬─────────────────┐
│ Hostname        │ MAC Address      │ Static IP       │
├─────────────────┼──────────────────┼─────────────────┤
│ train-server    │ aa:bb:cc:dd:ee:01│ 192.168.1.10    │
│ rpi-train-01    │ aa:bb:cc:dd:ee:02│ 192.168.1.101   │
│ rpi-train-02    │ aa:bb:cc:dd:ee:03│ 192.168.1.102   │
│ rpi-train-03    │ aa:bb:cc:dd:ee:04│ 192.168.1.103   │
└─────────────────┴──────────────────┴─────────────────┘
```

**How to set up:**

1. Get MAC addresses: `ssh pi@<temp-ip> ip link show eth0`
2. Configure DHCP reservations in router
3. Reboot RPi devices

**Ansible Inventory:**

```yaml
# infra/ansible/inventory/production/hosts.yml
all:
  children:
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
          train_id: "train-001"

        rpi-train-02:
          ansible_host: 192.168.1.102
          ansible_user: pi
          train_id: "train-002"
```

---

#### Approach 2: mDNS/Avahi (Zero-Configuration Networking)

**Best for:** Development and discovery

**How it works:**

- Each RPi broadcasts its hostname on `<hostname>.local`
- No central DNS server needed
- Works out-of-the-box on Raspberry Pi OS

**Ansible Inventory:**

```yaml
# infra/ansible/inventory/staging/hosts.yml
all:
  children:
    edge:
      hosts:
        rpi-train-01:
          ansible_host: rpi-train-01.local
          ansible_user: pi
```

**Pros:**
✅ No router configuration needed  
✅ Auto-discovery  
✅ Works across network segments (with avahi-daemon)  

**Cons:**
❌ Less reliable than static IPs  
❌ Requires `.local` suffix  
❌ May have issues on some networks  

**Ensure Avahi is running:**

```yaml
# playbooks/provision_pi.yml
- name: Install Avahi (mDNS)
  apt:
    name:
      - avahi-daemon
      - avahi-utils
    state: present

- name: Enable Avahi
  systemd:
    name: avahi-daemon
    enabled: yes
    state: started
```

---

### Recommended Hybrid: Static IPs + Hostname Setup

**Provision playbook sets hostnames:**

```yaml
# playbooks/provision_pi.yml
- name: Set hostname
  hostname:
    name: "{{ inventory_hostname }}"

- name: Update /etc/hosts
  lineinfile:
    path: /etc/hosts
    line: "127.0.1.1 {{ inventory_hostname }}"
    regexp: '^127\.0\.1\.1'
```

**Use static IPs in production inventory:**

```yaml
# inventory/production/hosts.yml
ansible_host: 192.168.1.101  # Static IP
```

**Use mDNS in staging inventory:**

```yaml
# inventory/staging/hosts.yml
ansible_host: rpi-train-01.local  # mDNS discovery
```

---

### Decision: **Static DHCP Reservations (Production) + mDNS (Dev)**

**Implementation:**

1. Document MAC address collection in runbook
2. Create provision playbook to set hostnames
3. Use separate inventories for staging vs production

---

## 4. Troubleshooting Without Centralized Logging

### Requirement
>
> "Later is fine if you feel we can troubleshoot deployment without me having to copy/paste error messages."

### Built-in Ansible Debugging (Sufficient for Phase 1)

#### Level 1: Standard Verbose Output

```bash
# Run playbook with verbosity
ansible-playbook -i inventory/production deploy_edge.yml -v   # Basic
ansible-playbook -i inventory/production deploy_edge.yml -vv  # More detail
ansible-playbook -i inventory/production deploy_edge.yml -vvv # Debug
```

#### Level 2: Log to File

```yaml
# ansible.cfg
[defaults]
log_path = /var/log/ansible/deployment.log
```

#### Level 3: Structured Error Handling

```yaml
# playbooks/deploy_edge.yml
- name: Deploy edge controller
  docker_container:
    name: edge-controller
    image: "{{ edge_image }}"
    state: started
  register: deploy_result
  failed_when: false  # Don't fail immediately

- name: Show deployment status
  debug:
    msg: |
      Deployment {{ 'succeeded' if deploy_result.failed == false else 'failed' }}
      Container ID: {{ deploy_result.container.Id | default('N/A') }}
      Error: {{ deploy_result.msg | default('None') }}
  when: deploy_result is defined

- name: Fail if deployment didn't work
  fail:
    msg: "Container deployment failed: {{ deploy_result.msg }}"
  when: deploy_result.failed
```

#### Level 4: Gather Docker Logs on Failure

```yaml
- name: Get container logs if failed
  command: docker logs edge-controller
  register: container_logs
  when: deploy_result.failed
  ignore_errors: yes

- name: Save logs to local file
  local_action:
    module: copy
    content: "{{ container_logs.stdout }}"
    dest: "./logs/{{ inventory_hostname }}-{{ ansible_date_time.iso8601 }}.log"
  when: deploy_result.failed
```

---

### Phase 2: Centralized Logging (When Needed)

**Recommended Stack: Loki + Promtail + Grafana**

```yaml
# infra/docker/docker-compose.observability.yml
services:
  loki:
    image: grafana/loki:latest
    ports:
      - "3100:3100"
    volumes:
      - loki_data:/loki

  grafana:
    image: grafana/grafana:latest
    ports:
      - "3001:3000"
    environment:
      GF_AUTH_ANONYMOUS_ENABLED: "true"
    volumes:
      - grafana_data:/var/lib/grafana

# Deploy Promtail to each RPi
# Sends logs to Loki
```

**Trigger for Phase 2:**

- More than 5 RPi devices
- Frequent debugging needed
- Need historical log analysis

---

### Decision: **Ansible Verbose Mode (Now) → Loki Stack (Phase 2)**

**Why it works:**

- Ansible `-vvv` shows full execution trace
- Failed tasks can capture Docker logs automatically
- Logs saved to local files for debugging
- When you hit 5+ devices, add Loki

---

## 5. Summary: Deployment Stack

### Final Architecture

```
┌─────────────────────────────────────────────────────────────┐
│ Developer Workstation                                       │
│ ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐  │
│ │ Git Repo    │  │ Ansible     │  │ GitHub Actions      │  │
│ │ (Source)    │→ │ (Deploy)    │  │ (Build Images)      │  │
│ └─────────────┘  └─────────────┘  └─────────────────────┘  │
│                         │                      │            │
└─────────────────────────┼──────────────────────┼────────────┘
                          │                      │
                          │                      ▼
                          │           ┌──────────────────────┐
                          │           │ GitHub Container     │
                          │           │ Registry (GHCR)      │
                          │           │ - central-api:latest │
                          │           │ - edge-controller:   │
                          │           │   latest (ARM64)     │
                          │           └──────────────────────┘
                          │                      │
                          ▼                      │
┌─────────────────────────────────────────┐     │
│ Central Host (192.168.1.10)             │     │
│ ┌───────────────┐  ┌─────────────────┐ │     │
│ │ central_api   │  │ mosquitto       │ │◄────┘
│ │ (Docker)      │  │ (Docker)        │ │
│ └───────────────┘  └─────────────────┘ │
│                                         │
│ [Ansible Vault Secrets - Encrypted]    │
└─────────────────────────────────────────┘
                          │
                          │ MQTT (1883)
                          │
              ┌───────────┴───────────┐
              │                       │
┌─────────────▼─────┐   ┌─────────────▼─────┐
│ rpi-train-01      │   │ rpi-train-02      │
│ (192.168.1.101)   │   │ (192.168.1.102)   │
│ ┌───────────────┐ │   │ ┌───────────────┐ │
│ │edge-controller│ │   │ │edge-controller│ │
│ │(Docker/ARM64) │ │   │ │(Docker/ARM64) │ │
│ └───────────────┘ │   │ └───────────────┘ │
│                   │   │                   │
│ [Static IP +      │   │ [Static IP +      │
│  mDNS hostname]   │   │  mDNS hostname]   │
└───────────────────┘   └───────────────────┘
```

### Component Matrix

| Component | Technology | Why | When to Change |
|-----------|-----------|-----|----------------|
| **Orchestration** | Ansible | Idempotent, testable | Never (unless K8s) |
| **Secrets** | Ansible Vault | Simple, local | >20 devices → Vault |
| **Registry** | GHCR | Free, no infra | Air-gap → local registry |
| **Networking** | Static IPs | Reliable | Never |
| **Logging** | Ansible -vvv | Built-in | >5 devices → Loki |

---

## Next Steps: Implementation Roadmap

### Week 1: Foundation

- [x] Research deployment approaches
- [x] Make architecture decisions
- [ ] Create Ansible directory structure
- [ ] Write provision playbook (install Docker, set hostname)
- [ ] Set up GHCR with GitHub Actions
- [ ] Create Ansible Vault for secrets

### Week 2: Central Deployment

- [ ] Write deploy_central.yml playbook
- [ ] Test on staging environment
- [ ] Document runbook
- [ ] Add health checks

### Week 3: Edge Deployment

- [ ] Write deploy_edge.yml playbook
- [ ] Test on 1 RPi
- [ ] Test on multiple RPi in parallel
- [ ] Add rollback playbook

### Week 4: Integration & Testing

- [ ] Create CI/CD workflow for deployment validation
- [ ] Write troubleshooting guide
- [ ] Test full deployment from scratch
- [ ] Document migration to Vault/Loki (future)

---

## Open Questions (Answered)

| Question | Answer | Implementation |
|----------|--------|----------------|
| Fixed IPs or DNS? | Static DHCP + mDNS | Set up in provision playbook |
| Secrets storage? | Ansible Vault | Create `secrets/vault.yml` |
| Container registry? | GHCR | GitHub Actions workflow |
| RPi offline? | No | Can pull images directly |
| Centralized logs? | Phase 2 | Use Ansible `-vvv` for now |

---

## Reference Links

- [Ansible Vault Documentation](https://docs.ansible.com/ansible/latest/vault_guide/index.html)
- [GitHub Container Registry Docs](https://docs.github.com/en/packages/working-with-a-github-packages-registry/working-with-the-container-registry)
- [Ansible Docker Modules](https://docs.ansible.com/ansible/latest/collections/community/docker/index.html)
- [Raspberry Pi Static IP Setup](https://www.raspberrypi.com/documentation/computers/configuration.html#setting-up-a-static-ip-address)
- [Avahi/mDNS on Raspberry Pi](https://www.raspberrypi.com/documentation/computers/remote-access.html#resolving-raspberrypi-local-with-mdns)

---

**Status:** ✅ **READY FOR IMPLEMENTATION**

All architectural decisions are made. Proceed to Ansible playbook development.
