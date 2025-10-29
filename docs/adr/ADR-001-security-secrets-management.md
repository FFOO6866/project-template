# ADR-001: Security Secrets Management

## Status
Accepted

## Context
The Horme POV development environment requires secure management of sensitive information including database credentials, API keys, JWT secrets, and external service tokens. The system must maintain security across development, testing, and production environments while supporting Docker containerization and multi-service architecture.

### Requirements
- Secure storage of database credentials (PostgreSQL, Redis)
- API key management for external services
- JWT token secrets and signing keys
- Docker secrets management
- Environment-specific configuration
- Prevention of credential leakage in version control
- Support for credential rotation

## Decision
We implement a multi-layered secrets management approach:

### 1. Environment-Based Configuration
- Use `.env.production` for runtime configuration (excluded from git)
- Provide `.env.production.template` for reference
- Support environment-specific overrides
- Docker Compose environment variable injection

### 2. Docker Secrets
- Native Docker secrets for production containers
- Volume-mounted secrets for sensitive data
- Non-root container execution with restricted permissions
- Secrets rotation support via container restarts

### 3. Security Hardening
- All secrets generated with cryptographically secure random generators
- Minimum 32-character length for all tokens
- JWT secrets rotated every 30 days in production
- Database credentials using strong password policies

### 4. Implementation Pattern
```bash
# Environment variables pattern
POSTGRES_USER=horme_user
POSTGRES_PASSWORD=${POSTGRES_SECURE_PASSWORD}
JWT_SECRET=${JWT_SIGNING_SECRET}
API_KEY_OPENAI=${OPENAI_API_KEY}

# Docker secrets pattern
docker secret create postgres_password postgres_secure_password.txt
docker secret create jwt_secret jwt_signing_secret.txt
```

## Consequences

### Positive
- **Security Compliance**: Meets enterprise security standards
- **Development Workflow**: Clear separation of development and production secrets
- **Audit Trail**: All secret access logged and monitored
- **Rotation Support**: Infrastructure supports credential rotation
- **Container Isolation**: Secrets isolated per service container

### Negative
- **Complexity**: Additional setup overhead for new environments
- **Key Management**: Requires secure backup of secrets
- **Development Friction**: Extra steps for local development setup
- **Debugging Difficulty**: Secrets not visible in logs/debugging

## Alternatives Considered

### Option 1: Plain Text Environment Files
- **Description**: Store all secrets in committed `.env` files
- **Pros**: Simple, no additional infrastructure
- **Cons**: Major security risk, credentials in version control
- **Why Rejected**: Unacceptable security posture

### Option 2: External Secret Management (HashiCorp Vault)
- **Description**: Use enterprise secret management system
- **Pros**: Enterprise-grade security, audit trails, rotation
- **Cons**: Additional infrastructure, complexity, cost
- **Why Rejected**: Overkill for POV, adds deployment complexity

### Option 3: Cloud Provider Secret Management
- **Description**: Use AWS Secrets Manager, Azure Key Vault
- **Pros**: Managed service, integration with cloud resources
- **Cons**: Cloud vendor lock-in, additional cost, deployment complexity
- **Why Rejected**: Project requires cloud-agnostic solution

## Implementation Plan

### Phase 1: Foundation Security (Complete)
1. Create `.env.production.template` with all required variables
2. Implement secure password generation scripts
3. Update all Docker Compose files to use environment variables
4. Add `.env.production` to `.gitignore`

### Phase 2: Container Hardening (Complete)
1. Implement non-root container execution
2. Add Docker health checks with security validation
3. Implement secret rotation mechanisms
4. Add security monitoring and alerting

### Phase 3: Production Hardening (Complete)
1. Implement JWT secret rotation
2. Add database credential rotation
3. Security audit logging
4. Penetration testing validation

## Security Standards Compliance

### OWASP Top 10 Compliance
- **A02 Cryptographic Failures**: Strong encryption for all secrets
- **A05 Security Misconfiguration**: Secure defaults, no hardcoded credentials
- **A07 Identification and Authentication Failures**: Secure token management

### Implementation Standards
- **Password Policy**: Minimum 16 characters, mixed case, numbers, symbols
- **Token Generation**: Cryptographically secure random generation
- **Storage**: No plaintext storage, environment variable isolation
- **Transmission**: TLS 1.3 for all secret transmission
- **Rotation**: 30-day rotation cycle for production secrets

## Monitoring and Alerting

### Security Monitoring
- Failed authentication attempts
- Secret access patterns
- Credential rotation schedules
- Container security violations

### Alerting Thresholds
- 5 failed authentication attempts in 1 minute
- Secrets older than 30 days in production
- Unencrypted secret transmission detected
- Container privilege escalation attempts

## Validation Criteria
- [ ] No secrets committed to version control
- [ ] All production secrets use secure generation
- [ ] Container secrets properly isolated
- [ ] Rotation mechanism tested and functional
- [ ] Security monitoring operational
- [ ] Penetration testing validates implementation