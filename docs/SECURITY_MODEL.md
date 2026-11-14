# COBBS Intelligence — Security Model

## Trust boundaries

- JWT auth; RBAC + organization membership
- Tenant isolation via organization_id filters
- AI output advisory only
- PRODUCTION requires approval
- SSRF blocks private/loopback/metadata; DNS rebinding checks
- Assessment deny-by-default without TargetScope
- Remediation: no self-approve/self-verify
- Hash-chained audit (not DBA-proof — documented)
