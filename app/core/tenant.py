import uuid
from dataclasses import dataclass
from typing import Any
from fastapi import Depends, Header, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
import jwt

from app.core.config import settings
from app.core.database import AsyncSessionLocal
from app.core.security import decode_access_token

security_bearer = HTTPBearer(auto_error=False)


@dataclass
class TenantContext:
    session: AsyncSession
    tenant_id: uuid.UUID
    tenant_slug: str
    tenant_name: str


@dataclass
class AuthenticatedContext:
    session: AsyncSession
    tenant_id: uuid.UUID
    user_id: uuid.UUID
    role: str
    email: str
    full_name: str


async def get_tenant_db(x_tenant_id: str = Header(default="public")) -> Any:
    """
    Extracts tenant slug from X-Tenant-ID header.
    Validates tenant and establishes a transaction with 'app.current_tenant_id'
    bound via SET LOCAL so PostgreSQL Row-Level Security (RLS) is strictly enforced.
    """
    tenant_slug = x_tenant_id.strip().lower()
    async with AsyncSessionLocal() as session:
        async with session.begin():
            res = await session.execute(
                text("SELECT id, slug, name, is_active FROM tenants WHERE slug = :s"),
                {"s": tenant_slug}
            )
            row = res.first()
            if not row or not row.is_active:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Institution/Tenant '{tenant_slug}' is not found or inactive."
                )
            
            # Bind transaction-local tenant context for PostgreSQL RLS policies
            await session.execute(
                text("SELECT set_config('app.current_tenant_id', :tid, true)"),
                {"tid": str(row.id)}
            )
            
            yield TenantContext(
                session=session,
                tenant_id=row.id,
                tenant_slug=row.slug,
                tenant_name=row.name
            )


async def get_current_user(
    auth: HTTPAuthorizationCredentials | None = Depends(security_bearer),
    tenant: TenantContext = Depends(get_tenant_db)
) -> AuthenticatedContext:
    """
    Validates JWT token and ensures the token belongs strictly to the requested tenant.
    Guarantees that a token issued for Tenant A cannot be used to query Tenant B.
    """
    if not auth or not auth.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication token is missing. Please log in.",
            headers={"WWW-Authenticate": "Bearer"}
        )
        
    try:
        payload = decode_access_token(auth.credentials)
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session expired. Please log in again.",
            headers={"WWW-Authenticate": "Bearer"}
        )
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token.",
            headers={"WWW-Authenticate": "Bearer"}
        )
        
    token_tenant_id = payload.get("tid")
    if token_tenant_id != str(tenant.tenant_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: Cross-tenant token mismatch."
        )
        
    user_id_str = payload.get("sub")
    if not user_id_str:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Malformed token payload.")
        
    user_id = uuid.UUID(user_id_str)
    
    # Retrieve user from tenant-scoped database
    res = await tenant.session.execute(
        text("SELECT id, email, full_name, role, is_active FROM users WHERE id = :uid AND tenant_id = :tid"),
        {"uid": user_id, "tid": tenant.tenant_id}
    )
    user_row = res.first()
    if not user_row or not user_row.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User account is deactivated or not found.")
        
    return AuthenticatedContext(
        session=tenant.session,
        tenant_id=tenant.tenant_id,
        user_id=user_row.id,
        role=user_row.role,
        email=user_row.email,
        full_name=user_row.full_name
    )


def require_roles(*allowed_roles: str):
    """Factory dependency to enforce role-based access control (RBAC)."""
    async def role_checker(ctx: AuthenticatedContext = Depends(get_current_user)) -> AuthenticatedContext:
        if ctx.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Operation requires one of the following roles: {', '.join(allowed_roles)}"
            )
        return ctx
    return role_checker

