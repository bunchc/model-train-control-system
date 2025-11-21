# Security Policy

## Supported Versions

We actively support the following versions with security updates:

| Version | Supported          |
| ------- | ------------------ |
| 0.1.x   | :white_check_mark: |
| < 0.1   | :x:                |

## Reporting a Vulnerability

**Please do not report security vulnerabilities through public GitHub issues.**

Instead, please report them via the GitHub Security Advisories feature or contact the maintainer directly.

You should receive a response within 48 hours. If for some reason you do not, please follow up to ensure we received your original message.

Please include the following information:

- Type of issue (e.g., buffer overflow, SQL injection, cross-site scripting, etc.)
- Full paths of source file(s) related to the manifestation of the issue
- The location of the affected source code (tag/branch/commit or direct URL)
- Any special configuration required to reproduce the issue
- Step-by-step instructions to reproduce the issue
- Proof-of-concept or exploit code (if possible)
- Impact of the issue, including how an attacker might exploit it

## Security Update Process

1. Security vulnerabilities are triaged within 48 hours
2. A fix is developed and tested in a private repository
3. A security advisory is published
4. The fix is released and all supported versions are updated
5. Users are notified via GitHub Security Advisories

## Security Best Practices

### For Edge Controllers (Raspberry Pi)

1. **Hardware Access**: Never expose GPIO control endpoints to untrusted networks
2. **MQTT Authentication**: Always use username/password for MQTT broker connections
3. **TLS/SSL**: Use TLS for MQTT connections in production environments
4. **Firmware Updates**: Keep Raspberry Pi OS and all packages up to date
5. **Network Segmentation**: Isolate edge controllers on a dedicated VLAN
6. **Physical Security**: Ensure physical access to controllers is restricted
7. **Configuration Management**: Store configuration files securely, never commit secrets

### For Central API

1. **Authentication**: Implement proper API authentication (JWT, API keys)
2. **Rate Limiting**: Protect against DoS attacks with appropriate rate limits
3. **Input Validation**: Validate all inputs using Pydantic models
4. **SQL Injection**: Use parameterized queries (already implemented via SQLite)
5. **CORS**: Configure CORS appropriately for your deployment environment
6. **HTTPS**: Always use HTTPS in production deployments
7. **Secrets Management**: Use environment variables or secret management systems

### For Developers

1. **Dependencies**: Run `make security` before committing code
2. **Secrets**: Never commit secrets, API keys, or passwords to version control
3. **Code Review**: All PRs require security review before merging
4. **Testing**: Write security-focused test cases for sensitive functionality
5. **Pre-commit Hooks**: Install and use the provided pre-commit configuration
6. **Keep Updated**: Regularly update dependencies to patch known vulnerabilities

## Automated Security Scanning

This project uses multiple automated security tools:

- **Bandit**: Python security linting (runs on every PR)
- **Safety**: Dependency vulnerability scanning (weekly via Dependabot)
- **Trivy**: Container vulnerability scanning (runs on every build)
- **Dependabot**: Automated dependency updates (weekly)
- **Gitleaks**: Secret detection (runs on every commit via pre-commit)
- **Ruff**: Includes security linting rules (S-prefix rules)

## Security Headers

For production deployments, ensure the following headers are set:

```text
Strict-Transport-Security: max-age=31536000; includeSubDomains
X-Content-Type-Options: nosniff
X-Frame-Options: DENY
X-XSS-Protection: 1; mode=block
Content-Security-Policy: default-src 'self'
```

## MQTT Security

### Broker Configuration

- Enable authentication on MQTT broker
- Use TLS/SSL encryption for all connections
- Implement ACLs (Access Control Lists) to restrict topic access
- Monitor connection attempts and failed authentications
- Use strong passwords (minimum 16 characters)

### Client Security

- Store MQTT credentials securely (environment variables, not hardcoded)
- Validate all incoming MQTT messages
- Implement message size limits
- Use QoS levels appropriately
- Handle connection failures gracefully

## Container Security

### Best Practices

1. **Base Images**: Use official, minimal base images (Alpine, Distroless)
2. **Layer Scanning**: All images scanned with Trivy before deployment
3. **Non-Root User**: Containers run as non-root users
4. **Read-Only Filesystem**: Where possible, use read-only root filesystem
5. **Resource Limits**: Set appropriate CPU and memory limits
6. **Secrets**: Use Docker secrets or Kubernetes secrets, never build them into images

### Regular Scanning

- CI/CD pipeline scans all container builds
- Fails build on CRITICAL vulnerabilities
- Weekly scans of deployed images
- SBOM (Software Bill of Materials) generated for all images

## Incident Response

In the event of a security incident:

1. **Immediate Actions**:
   - Isolate affected systems
   - Preserve logs and evidence
   - Notify security team immediately

2. **Investigation**:
   - Determine scope and impact
   - Identify root cause
   - Document timeline of events

3. **Remediation**:
   - Patch vulnerability
   - Update affected systems
   - Verify fix effectiveness

4. **Post-Incident**:
   - Conduct post-mortem analysis
   - Update security procedures
   - Communicate with affected users

## Compliance

This project follows industry-standard security practices:

- **OWASP Top 10**: Security guidelines for web applications
- **CIS Docker Benchmark**: Container security best practices
- **NIST Cybersecurity Framework**: Overall security posture
- **OWASP IoT Top 10**: Security for IoT/edge devices

## Security Checklist for Deployments

### Pre-Deployment

- [ ] All dependencies scanned for vulnerabilities
- [ ] Container images scanned with Trivy
- [ ] Security tests passing
- [ ] Secrets managed via secure methods
- [ ] Network segmentation configured
- [ ] TLS/SSL certificates valid

### Post-Deployment

- [ ] Monitoring and alerting configured
- [ ] Log aggregation enabled
- [ ] Backup procedures tested
- [ ] Incident response plan documented
- [ ] Security contacts updated

## Contact

For security concerns:

- Use GitHub Security Advisories
- Contact repository maintainers

For general questions:

- Use GitHub Discussions
- Open a regular issue (for non-security topics)

## Acknowledgments

We appreciate responsible disclosure and will acknowledge security researchers who report vulnerabilities to us in a responsible manner.

## Version History

- **v0.1.0** (2025-11-20): Initial security policy
