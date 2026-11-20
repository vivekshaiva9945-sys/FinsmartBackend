import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import text

from app.core.tenant import AuthenticatedContext, get_current_user
from app.schemas.account import AccountCreate, AccountOut

router = APIRouter()


@router.get("", response_model=list[AccountOut], include_in_schema=False)
@router.get("/", response_model=list[AccountOut])
async def list_accounts(ctx: AuthenticatedContext = Depends(get_current_user)):
    """List all active accounts (Bank, Cash, Wallets) for the current user."""
    res = await ctx.session.execute(
        text("""
            SELECT id, name, account_type, balance_minor, currency, is_active, created_at
            FROM accounts
            WHERE user_id = :u AND is_active = true
            ORDER BY created_at ASC
        """),
        {"u": ctx.user_id}
    )
    return [AccountOut(**dict(r._mapping)) for r in res.all()]


@router.post("", response_model=AccountOut, status_code=status.HTTP_201_CREATED, include_in_schema=False)
@router.post("/", response_model=AccountOut, status_code=status.HTTP_201_CREATED)
async def create_account(payload: AccountCreate, ctx: AuthenticatedContext = Depends(get_current_user)):
    """Create a new financial tracking account."""
    acc_id = uuid.uuid4()
    res = await ctx.session.execute(
        text("""
            INSERT INTO accounts (id, tenant_id, user_id, name, account_type, balance_minor)
            VALUES (:id, :t, :u, :name, :type, :balance)
            RETURNING id, name, account_type, balance_minor, currency, is_active, created_at
        """),
        {
            "id": acc_id,
            "t": ctx.tenant_id,
            "u": ctx.user_id,
            "name": payload.name.strip(),
            "type": payload.account_type,
            "balance": payload.initial_balance_minor
        }
    )
    row = res.one()
    return AccountOut(**dict(row._mapping))

