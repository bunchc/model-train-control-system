#!/usr/bin/env bash
#
# Deployment Wrapper Script for Model Train Control System
#
# Simplified interface for Ansible deployment operations
#
# Usage:
#   ./scripts/deploy.sh provision [host]     # Provision RPi devices
#   ./scripts/deploy.sh central              # Deploy central infrastructure
#   ./scripts/deploy.sh edge [host]          # Deploy edge controllers
#   ./scripts/deploy.sh update [central|edge]  # Update deployments
#   ./scripts/deploy.sh rollback <version>   # Rollback to version
#   ./scripts/deploy.sh status               # Show deployment status

set -euo pipefail

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
ANSIBLE_DIR="${PROJECT_ROOT}/infra/ansible"

# Default values
INVENTORY="${INVENTORY:-production}"
ANSIBLE_VAULT_PASS="${ANSIBLE_VAULT_PASSWORD_FILE:-}"

# ============================================================================
# Helper Functions
# ============================================================================

log_info() {
    echo -e "${CYAN}[INFO]${NC} $*"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $*"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $*" >&2
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $*"
}

check_requirements() {
    if ! command -v ansible-playbook &> /dev/null; then
        log_error "Ansible is not installed. Install with: pip install ansible"
        exit 1
    fi

    if [ ! -d "${ANSIBLE_DIR}" ]; then
        log_error "Ansible directory not found: ${ANSIBLE_DIR}"
        exit 1
    fi
}

get_vault_pass_arg() {
    if [ -n "${ANSIBLE_VAULT_PASS}" ]; then
        echo "--vault-password-file ${ANSIBLE_VAULT_PASS}"
    else
        echo "--ask-vault-pass"
    fi
}

run_playbook() {
    local playbook=$1
    shift
    local extra_args=("$@")

    log_info "Running playbook: ${playbook}"
    log_info "Inventory: ${INVENTORY}"

    cd "${ANSIBLE_DIR}"

    # shellcheck disable=SC2046
    ansible-playbook \
        -i "inventory/${INVENTORY}/hosts.yml" \
        "playbooks/${playbook}" \
        $(get_vault_pass_arg) \
        "${extra_args[@]}"
}

# ============================================================================
# Command Functions
# ============================================================================

provision() {
    local limit_host=${1:-}

    log_info "Provisioning Raspberry Pi devices..."

    if [ -n "${limit_host}" ]; then
        log_info "Limiting to host: ${limit_host}"
        run_playbook "provision_pi.yml" --limit "${limit_host}"
    else
        log_warning "This will provision ALL edge devices in the inventory"
        read -p "Continue? (y/N) " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            log_info "Cancelled"
            exit 0
        fi
        run_playbook "provision_pi.yml"
    fi

    log_success "Provisioning complete!"
}

deploy_central() {
    log_info "Deploying central infrastructure (API + MQTT)..."

    run_playbook "deploy_central.yml"

    log_success "Central infrastructure deployed!"
    log_info "Check status with: docker compose -f /opt/train-control/docker-compose.yml ps"
}

deploy_edge() {
    local limit_host=${1:-}

    log_info "Deploying edge controllers..."

    if [ -n "${limit_host}" ]; then
        log_info "Limiting to host: ${limit_host}"
        run_playbook "deploy_edge.yml" --limit "${limit_host}"
    else
        log_warning "This will deploy to ALL edge devices in the inventory"
        read -p "Continue? (y/N) " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            log_info "Cancelled"
            exit 0
        fi
        run_playbook "deploy_edge.yml"
    fi

    log_success "Edge controllers deployed!"
}

update() {
    local component=${1:-all}

    case "${component}" in
        central)
            log_info "Updating central infrastructure..."
            run_playbook "update.yml" --tags central
            ;;
        edge)
            log_info "Updating edge controllers..."
            run_playbook "update.yml" --tags edge
            ;;
        all)
            log_info "Updating all components..."
            run_playbook "update.yml"
            ;;
        *)
            log_error "Invalid component: ${component}"
            log_info "Valid options: central, edge, all"
            exit 1
            ;;
    esac

    log_success "Update complete!"
}

rollback() {
    local version=${1:-}

    if [ -z "${version}" ]; then
        log_error "Version required for rollback"
        log_info "Usage: $0 rollback <version>"
        log_info "Example: $0 rollback v1.2.0"
        exit 1
    fi

    log_warning "Rolling back to version: ${version}"
    read -p "Continue? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        log_info "Cancelled"
        exit 0
    fi

    run_playbook "rollback.yml" --extra-vars "version=${version}"

    log_success "Rollback complete!"
}

status() {
    log_info "Checking deployment status..."

    cd "${ANSIBLE_DIR}"

    log_info "Pinging all hosts..."
    ansible all -i "inventory/${INVENTORY}/hosts.yml" -m ping

    log_info ""
    log_info "Getting Docker container status..."
    ansible all -i "inventory/${INVENTORY}/hosts.yml" \
        -a "docker ps --format 'table {{.Names}}\t{{.Status}}'" \
        --become
}

show_help() {
    cat << EOF
Model Train Control System - Deployment Script

Usage:
    $0 <command> [options]

Commands:
    provision [host]         Provision Raspberry Pi devices
                            Optional: limit to specific host

    central                  Deploy central infrastructure (API + MQTT)

    edge [host]              Deploy edge controllers
                            Optional: limit to specific host

    update [component]       Update deployments (central, edge, or all)

    rollback <version>       Rollback to specific version
                            Example: $0 rollback v1.2.0

    status                   Check deployment status of all hosts

    help                     Show this help message

Environment Variables:
    INVENTORY                Inventory to use (default: production)
                            Options: production, staging

    ANSIBLE_VAULT_PASSWORD_FILE  Path to vault password file
                                If not set, will prompt for password

Examples:
    # Provision all RPi devices
    $0 provision

    # Provision specific device
    $0 provision rpi-train-01

    # Deploy central infrastructure
    $0 central

    # Deploy to all edge devices
    $0 edge

    # Deploy to specific edge device
    $0 edge rpi-train-02

    # Update everything
    $0 update all

    # Update only edge controllers
    $0 update edge

    # Rollback edge controllers to version
    $0 rollback v1.2.0

    # Check status
    $0 status

    # Use staging inventory
    INVENTORY=staging $0 edge

For more information, see: docs/deployment-runbook.md
EOF
}

# ============================================================================
# Main Script
# ============================================================================

main() {
    check_requirements

    local command=${1:-help}
    shift || true

    case "${command}" in
        provision)
            provision "$@"
            ;;
        central)
            deploy_central
            ;;
        edge)
            deploy_edge "$@"
            ;;
        update)
            update "$@"
            ;;
        rollback)
            rollback "$@"
            ;;
        status)
            status
            ;;
        help|--help|-h)
            show_help
            ;;
        *)
            log_error "Unknown command: ${command}"
            echo ""
            show_help
            exit 1
            ;;
    esac
}

main "$@"
