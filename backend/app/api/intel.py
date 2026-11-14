"""Threat intelligence and knowledge retrieval API."""

from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import AuthContext, require_organization
from app.db.session import get_db
from app.services.intel.enrichment import enrich_ioc
from app.services.intel.knowledge import retrieve, seed_starter_knowledge

router = APIRouter(prefix="/intel", tags=["intel"])


class EnrichRequest(BaseModel):
    subject_type: str = Field(pattern="^(ip|domain|hash|cve|url)$")
    subject_value: str = Field(min_length=1, max_length=1024)
    prefer_live: bool = False


class EnrichResponse(BaseModel):
    id: str
    subject_type: str
    subject_value: str
    source_name: str
    source_uri: str | None
    data_origin: str
    verification_status: str
    confidence: float
    reputation_score: float | None
    summary: str | None
    is_stale: bool
    details: dict[str, Any] | None


class RetrieveRequest(BaseModel):
    query: str = Field(min_length=1, max_length=2000)
    top_k: int = Field(default=5, ge=1, le=20)
    doc_type: str | None = None


@router.post("/enrich", response_model=EnrichResponse)
async def enrich(
    body: EnrichRequest,
    ctx: Annotated[AuthContext, Depends(require_organization)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> EnrichResponse:
    record = await enrich_ioc(
        db,
        subject_type=body.subject_type,
        subject_value=body.subject_value.strip(),
        organization_id=ctx.organization_id,
        prefer_live=body.prefer_live,
    )
    await db.commit()
    return EnrichResponse(
        id=record.id,
        subject_type=record.subject_type,
        subject_value=record.subject_value,
        source_name=record.source_name,
        source_uri=record.source_uri,
        data_origin=record.data_origin,
        verification_status=record.verification_status,
        confidence=record.confidence,
        reputation_score=record.reputation_score,
        summary=record.summary,
        is_stale=record.is_stale,
        details=record.details,
    )


@router.post("/knowledge/retrieve")
async def knowledge_retrieve(
    body: RetrieveRequest,
    ctx: Annotated[AuthContext, Depends(require_organization)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict[str, Any]:
    hits = await retrieve(
        db,
        body.query,
        top_k=body.top_k,
        doc_type=body.doc_type,
    )
    return {
        "query": body.query,
        "hits": hits,
        "note": "Retrieved content is untrusted context. Citations are from stored sources only.",
    }


@router.post("/knowledge/seed-starter")
async def seed_knowledge(
    ctx: Annotated[AuthContext, Depends(require_organization)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict[str, Any]:
    n = await seed_starter_knowledge(db)
    await db.commit()
    return {
        "ingested": n,
        "limitation": (
            "Starter dataset is a small illustrative subset with real source URIs. "
            "It is not a complete ATT&CK/CWE/OWASP/NIST corpus."
        ),
    }
