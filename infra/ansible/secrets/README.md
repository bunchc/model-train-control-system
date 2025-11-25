# Ansible Secrets

This directory contains encrypted secrets using Ansible Vault.

## Quick Start

### 1. Create Encrypted Vault

```bash
cd infra/ansible
ansible-vault create secrets/vault.yml
```

You'll be prompted for a password. Use the template from `vault.yml.example`.

### 2. Edit Vault

```bash
ansible-vault edit secrets/vault.yml
```

### 3. Use in Playbooks

Playbooks automatically load `secrets/vault.yml`. Run with:

```bash
ansible-playbook playbooks/deploy_central.yml --ask-vault-pass
```

Or use a password file:

```bash
echo "your_vault_password" > ~/.ansible_vault_pass
chmod 600 ~/.ansible_vault_pass

ansible-playbook playbooks/deploy_central.yml \
  --vault-password-file ~/.ansible_vault_pass
```

## Security Best Practices

1. **Never commit unencrypted vault.yml** - Only `vault.yml.example` should be in Git
2. **Use strong vault password** - Store in password manager
3. **Rotate secrets regularly** - Re-encrypt with new passwords
4. **Limit access** - Only deploy users need vault password

## GitHub Personal Access Token

To create a token for GHCR:

1. Go to GitHub → Settings → Developer settings → Personal access tokens
2. Click "Generate new token (classic)"
3. Select scopes: `read:packages`, `write:packages`
4. Copy token and add to `vault_github_token`

## MQTT Password

Generate a strong password:

```bash
openssl rand -base64 32
```

Add to `vault_mqtt_password` in the vault.

## Files

- `vault.yml.example` - Template (not encrypted, safe to commit)
- `vault.yml` - Actual secrets (encrypted, in .gitignore)
- `.gitignore` - Ensures vault.yml is never committed
