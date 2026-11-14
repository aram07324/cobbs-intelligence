"""Vulnerability and risk API."""

from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import AuthContext, require_organization
from app.db.session import get_db
from app.models.vuln import CVERecord, Finding
from app.services.vuln.risk import create_or_update_finding, seed_starter_cves

router = APIRouter(prefix="/vuln", tags=["vuln"])


class FindingCreateRequest(BaseModel):
    title: str = Field(min_length=3, max_length=512)
    description: str | None = None
    category: str = "vulnerability"
    severity: str = Field(default="medium", pattern="^(critical|high|medium|low|info)$")
    cve_id: str | None = None
    asset_id: str | None = None
    confirmation_status: str = Field(
        default="suspected",
        pattern="^(suspected|confirmed|false_positive|accepted_risk)$",
    )
    confidence: float = Field(default=0.5, ge=0.0, le=1.0)
    evidence_ids: list[str] | None = None
    asset_criticality: float = Field(default=0.5, ge=0.0, le=1.0)
    internet_exposed: bool = False
    mark_false_positive: bool = False


class FindingResponse(BaseModel):
    id: str
    title: str
    category: str
    severity: str
    cve_id: str | None
    confirmation_status: str
    risk_score: float
    confidence: float
    risk_explanation: str | None
    status: str
    evidence_ids: list[Any] | None
    dedup_key: str

    model_config = {"from_attributes": True}


@router.post("/cves/seed-starter")
async def seed_cves(
    ctx: Annotated[AuthContext, Depends(require_organization)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict[str, Any]:
    n = await seed_starter_cves(db)
    await db.commit()
    return {
        "ingested": n,
        "limitation": "Starter CVE set is illustrative only; not a full NVD/KEV feed.",
    }


@router.get("/cves/{cve_id}")
async def get_cve(
    cve_id: str,
    ctx: Annotated[AuthContext, Depends(require_organization)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict[str, Any]:
    result = await db.execute(select(CVERecord).where(CVERecord.cve_id == cve_id.upper()))
    row = result.scalar_one_or_none()
    if not row:
        raise HTTPException(status_code=404, detail={"code": "not_found", "message": "CVE not in store"})
    return {
        "cve_id": row.cve_id,
        "description": row.description,
        "cvss_base_score": row.cvss_base_score,
        "severity": row.severity,
        "cwe_ids": row.cwe_ids,
        "is_kev": row.is_kev,
        "data_origin": row.data_origin,
        "verification_status": row.verification_status,
        "references": row.references,
    }


@router.post("/findings", response_model=FindingResponse, status_code=201)
async def create_finding(
    body: FindingCreateRequest,
    ctx: Annotated[AuthContext, Depends(require_organization)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> FindingResponse:
    finding = await create_or_update_finding(
        db,
        organization_id=ctx.organization_id,
        title=body.title,
        category=body.category,
        severity=body.severity,
        cve_id=body.cve_id,
        asset_id=body.asset_id,
        description=body.description,
        confirmation_status=body.confirmation_status,
        confidence=body.confidence,
        evidence_ids=body.evidence_ids,
        asset_criticality=body.asset_criticality,
        internet_exposed=body.internet_exposed,
        actor_id=ctx.user.id,
        mark_false_positive=body.mark_false_positive,
    )
    await db.commit()
    return FindingResponse.model_validate(finding)


@router.get("/findings", response_model=list[FindingResponse])
async def list_findings(
    ctx: Annotated[AuthContext, Depends(require_organization)],
    db: Annotated[AsyncSession, Depends(get_db)],
    limit: int = 50,
) -> list[FindingResponse]:
    limit = max(1, min(limit, 100))
    result = await db.execute(
        select(Finding)
        .where(Finding.organization_id == ctx.organization_id)
        .order_by(Finding.risk_score.desc())
        .limit(limit)
    )
    return [FindingResponse.model_validate(r) for r in result.scalars().all()]
