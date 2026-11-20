import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import text

from app.core.tenant import AuthenticatedContext, get_current_user
from app.schemas.consent import ConsentOut, ConsentUpdate

router = APIRouter()


@router.get("", response_model=list[ConsentOut], include_in_schema=False)
@router.get("/", response_model=list[ConsentOut])
async def list_consents(ctx: AuthenticatedContext = Depends(get_current_user)):
    """Fetch user active DPDP 2023 consent records."""
    res = await ctx.session.execute(
        text("SELECT id, purpose, granted, at FROM consents WHERE user_id = :u ORDER BY at DESC"),
        {"u": ctx.user_id}
    )
    return [ConsentOut(**dict(r._mapping)) for r in res.all()]


@router.post("/toggle", response_model=ConsentOut)
async def toggle_consent(payload: ConsentUpdate, ctx: AuthenticatedContext = Depends(get_current_user)):
    """Grant or revoke explicit consent for a data processing purpose."""
    consent_id = uuid.uuid4()
    res = await ctx.session.execute(
        text("""
            INSERT INTO consents (id, tenant_id, user_id, purpose, granted, at)
            VALUES (:id, :t, :u, :p, :g, now())
            RETURNING id, purpose, granted, at
        """),
        {
            "id": consent_id,
            "t": ctx.tenant_id,
            "u": ctx.user_id,
            "p": payload.purpose.strip().lower(),
            "g": payload.granted
        }
    )
    row = res.one()
    return ConsentOut(**dict(row._mapping))

