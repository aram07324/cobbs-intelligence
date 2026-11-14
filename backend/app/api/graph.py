"""Security evidence graph API."""

from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import AuthContext, require_organization
from app.db.session import get_db
from app.services.graph.edges import (
    GraphError,
    bounded_traverse,
    create_edge,
    neighbors,
)

router = APIRouter(prefix="/graph", tags=["graph"])


class EdgeCreateRequest(BaseModel):
    src_type: str
    src_id: str
    dst_type: str
    dst_id: str
    relation_type: str
    confidence: float = Field(default=0.5, ge=0.0, le=1.0)
    evidence_id: str | None = None
    details: dict[str, Any] | None = None
    notes: str | None = None


class EdgeResponse(BaseModel):
    id: str
    src_type: str
    src_id: str
    dst_type: str
    dst_id: str
    relation_type: str
    confidence: float
    evidence_id: str | None
    organization_id: str

    model_config = {"from_attributes": True}


class TraverseRequest(BaseModel):
    entity_type: str
    entity_id: str
    max_depth: int = Field(default=2, ge=1, le=4)


@router.post("/edges", response_model=EdgeResponse, status_code=201)
async def add_edge(
    body: EdgeCreateRequest,
    ctx: Annotated[AuthContext, Depends(require_organization)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> EdgeResponse:
    try:
        edge = await create_edge(
            db,
            organization_id=ctx.organization_id,
            src_type=body.src_type,
            src_id=body.src_id,
            dst_type=body.dst_type,
            dst_id=body.dst_id,
            relation_type=body.relation_type,
            confidence=body.confidence,
            evidence_id=body.evidence_id,
            details=body.details,
            notes=body.notes,
            actor_id=ctx.user.id,
        )
        await db.commit()
    except GraphError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": exc.code, "message": str(exc)},
        ) from exc
    return EdgeResponse(
        id=edge.id,
        src_type=edge.src_type,
        src_id=edge.src_id,
        dst_type=edge.dst_type,
        dst_id=edge.dst_id,
        relation_type=edge.relation_type,
        confidence=edge.confidence,
        evidence_id=edge.evidence_id,
        organization_id=edge.organization_id,
    )


@router.get("/neighbors")
async def get_neighbors(
    entity_type: str,
    entity_id: str,
    ctx: Annotated[AuthContext, Depends(require_organization)],
    db: Annotated[AsyncSession, Depends(get_db)],
    relation_type: str | None = None,
    direction: str = "both",
    include_historical: bool = False,
) -> dict[str, Any]:
    try:
        edges = await neighbors(
            db,
            organization_id=ctx.organization_id,
            entity_type=entity_type,
            entity_id=entity_id,
            relation_type=relation_type,
            direction=direction,
            include_historical=include_historical,
        )
    except GraphError as exc:
        raise HTTPException(status_code=400, detail={"code": exc.code, "message": str(exc)}) from exc
    return {
        "entity": {"type": entity_type, "id": entity_id},
        "edges": [
            {
                "id": e.id,
                "src_type": e.src_type,
                "src_id": e.src_id,
                "dst_type": e.dst_type,
                "dst_id": e.dst_id,
                "relation_type": e.relation_type,
                "confidence": e.confidence,
                "evidence_id": e.evidence_id,
                "valid_from": e.valid_from.isoformat() if e.valid_from else None,
                "valid_to": e.valid_to.isoformat() if e.valid_to else None,
            }
            for e in edges
        ],
    }


@router.post("/traverse")
async def traverse(
    body: TraverseRequest,
    ctx: Annotated[AuthContext, Depends(require_organization)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict[str, Any]:
    try:
        return await bounded_traverse(
            db,
            organization_id=ctx.organization_id,
            start_type=body.entity_type,
            start_id=body.entity_id,
            max_depth=body.max_depth,
        )
    except GraphError as exc:
        raise HTTPException(status_code=400, detail={"code": exc.code, "message": str(exc)}) from exc
