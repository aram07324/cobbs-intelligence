# COBBS INTELLIGENCE

Autonomous cybersecurity intelligence and engineering platform.

**Status:** Phase 1 — Foundation scaffolding (bootstrap complete).  
This is an early, non-operational scaffold. No security assessment, AI orchestration, asset discovery, or production capabilities are implemented yet.

## Mission

COBBS INTELLIGENCE combines:

- AI-powered security operations
- Threat intelligence & incident investigation
- Asset discovery & attack surface management
- Vulnerability assessment & remediation engineering
- Evidence correlation, contextual risk analysis
- Independent verification & continuous monitoring

Two integrated domains share auth, evidence, audit, storage, AI routing and governance:

- **COBBS CORE** — AI orchestration, alert analysis, threat intel, investigation, MITRE ATT&CK / ATLAS mapping, reporting
- **COBBS SECURITY** — Authorized asset discovery, attack surface management, vulnerability assessment, posture evaluation, remediation, isolated testing, verification, monitoring

## Current Scope (Phase 1)

- Modular monorepo layout
- FastAPI backend skeleton with settings, health endpoints, structured logging
- SQLAlchemy async + Alembic foundation
- Core models stubs (audit events with hash-chain support, evidence metadata)
- Docker Compose for local development (Postgres + pgvector, Redis)
- Basic test harness
- Security baseline (no secrets in repo, env example, resource limit placeholders)

**Not yet implemented:** authentication, AI providers, security scanners, workers beyond skeleton, frontend, real threat models, production approval flows.

## Tech Stack (preferred)

| Layer        | Technology                          |
|--------------|-------------------------------------|
| Backend      | Python 3.11+, FastAPI, Pydantic v2, SQLAlchemy async, Alembic, LangGraph, FastMCP |
| Frontend     | Next.js, React, TypeScript, Tailwind CSS |
| Data         | PostgreSQL + pgvector, Redis        |
| Workers      | ARQ (or equivalent bounded worker)  |
| Infra        | Docker Compose, OpenTelemetry       |
| AI           | Provider-independent adapters (xAI/Grok, OpenAI-compatible, Gemini, Groq, OpenRouter, Ollama) with FREE_FIRST mode |

## Quick Start (local)

```bash
# Prerequisites: Docker, Docker Compose, Python 3.11+, Node 20+

cp .env.example .env
# Edit .env as needed

docker compose -f infra/docker-compose.yml up -d postgres redis

cd backend
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
alembic upgrade head
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Health check: `curl http://localhost:8000/health`

## Engineering Rules (non-negotiable)

- Inspect existing code before changes
- Preserve working functionality
- Modular boundaries
- Real tests for every module; never invent successful test results
- Never hardcode credentials
- Never expose unrestricted shell/FS or Docker socket to AI workers
- Explicit authorization + scope for all security assessments
- Production modifications require approval + deterministic policy
- Treat external inputs as untrusted (SSRF, DNS rebinding, private network protections)
- Resource limits, timeouts, concurrency limits, tool-call budgets
- Evidence provenance + append-only hash-chained audit events
- Honest documentation of limitations
- Work only on the authorized phase; stop and wait for next authorization

## Repository Layout

```
.
├── backend/                 # FastAPI application
│   ├── app/
│   │   ├── api/             # Route modules
│   │   ├── core/            # Config, security, logging
│   │   ├── db/              # Session, base, migrations helpers
│   │   ├── models/          # SQLAlchemy models
│   │   ├── schemas/         # Pydantic schemas
│   │   ├── services/        # Business logic
│   │   └── workers/         # Background job entrypoints
│   ├── tests/
│   ├── alembic/
│   ├── pyproject.toml
│   └── Dockerfile
├── frontend/                # Next.js (placeholder)
├── infra/                   # Docker Compose, observability
├── packages/                # Shared libraries (future)
├── docs/                    # Architecture, ADRs, runbooks
├── scripts/                 # Utility scripts
├── .env.example
├── .gitignore
└── README.md
```

## Development Discipline

Phases are independently verifiable. After each phase:

1. Implementation + tests
2. Regression checks
3. Documentation update
4. Commit + push
5. Concise completion report
6. Stop and await authorization for the next phase

## License

Proprietary — all rights reserved (to be confirmed by project owner).

## Disclaimer

This software is under active controlled development. Do not use for production security operations until the corresponding phases are complete, tested, and explicitly authorized. No warranty is provided.
