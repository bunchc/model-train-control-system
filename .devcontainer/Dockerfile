FROM mcr.microsoft.com/vscode/devcontainers/base:ubuntu

ARG USERNAME=vscode
ARG USER_UID=1000
ARG USER_GID=$USER_UID

# Install basic packages, Python, Node.js, and Docker CLI
RUN apt-get update && export DEBIAN_FRONTEND=noninteractive \
  && apt-get install -y --no-install-recommends \
    curl ca-certificates git build-essential sudo python3 python3-pip python3-venv \
    gnupg2 lsb-release apt-transport-https \
  && curl -fsSL https://deb.nodesource.com/setup_18.x | bash - \
  && apt-get install -y nodejs \
  && npm install -g npm@latest \
  && apt-get clean && rm -rf /var/lib/apt/lists/*

# Create non-root user (vscode by default image usually has this)
RUN if id -u $USERNAME > /dev/null 2>&1; then echo "user exists"; else \
      useradd -m $USERNAME -u $USER_UID -s /bin/bash && echo "$USERNAME ALL=(ALL) NOPASSWD:ALL" > /etc/sudoers.d/$USERNAME ; fi

USER $USERNAME
WORKDIR /workspace
