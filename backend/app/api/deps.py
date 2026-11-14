"""FastAPI dependencies for authentication and authorization.

All authorization decisions happen here or in services — never trust the frontend.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import decode_access_token
from app.db.session import get_db
from app.models.identity import User
from app.services.auth import get_user_by_id

security_scheme = HTTPBearer(auto_error=False)


@dataclass
class AuthContext:
    user: User
    organization_id: str | None
    roles: list[str]
    token_payload: dict


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(security_scheme)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> AuthContext:
    if credentials is None or not credentials.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "unauthorized", "message": "Authentication required"},
            headers={"WWW-Authenticate": "Bearer"},
        )
    try:
        payload = decode_access_token(credentials.credentials)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "invalid_token", "message": "Invalid or expired token"},
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "invalid_token", "message": "Invalid token subject"},
        )

    user = await get_user_by_id(db, user_id)
    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "user_inactive", "message": "User not found or inactive"},
        )

    return AuthContext(
        user=user,
        organization_id=payload.get("org"),
        roles=payload.get("roles") or [],
        token_payload=payload,
    )


def require_roles(*allowed: str):
    async def _checker(ctx: Annotated[AuthContext, Depends(get_current_user)]) -> AuthContext:
        if ctx.user.is_superuser:
            return ctx
        if not any(r in ctx.roles for r in allowed):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "code": "forbidden",
                    "message": "Insufficient role",
                    "details": {"required": list(allowed), "have": ctx.roles},
                },
            )
        return ctx

    return _checker


async def require_organization(
    ctx: Annotated[AuthContext, Depends(get_current_user)],
) -> AuthContext:
    if not ctx.organization_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "code": "org_required",
                "message": "Organization context required",
            },
        )
    return ctx
