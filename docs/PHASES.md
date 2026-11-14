# COBBS Intelligence — Development Phases

Controlled, independently verifiable implementation plan.

## Phase 1 — Foundation Scaffolding (CURRENT)

**Status:** Complete (this commit)

Delivered:
- Monorepo layout
- FastAPI application factory, settings, structured logging
- Health / ready endpoints
- SQLAlchemy async + Alembic
- Core models: `audit_events` (hash-chained), `evidence`
- Audit service with deterministic SHA-256 chaining
- Docker Compose (Postgres + pgvector, Redis)
- Basic unit tests (config, health, audit chain)
- Security baseline (no secrets, env example, documented limitations)

**Not in scope:** Auth, AI providers, scanners, workers beyond skeleton, frontend, real findings.

## Future Phases (not yet authorized)

- Phase 2: Authentication & authorization foundation (users, roles, scopes)
- Phase 3: AI provider adapters + FREE_FIRST routing
- Phase 4: Evidence store & provenance hardening
- Phase 5: CORE alert ingestion & basic correlation
- Phase 6: SECURITY asset inventory (READ_ONLY)
- ... (further phases defined only when authorized)

Each phase must be authorized before work begins. After completion: tests, documentation, commit, push, report, stop.
