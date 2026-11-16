import datetime as dt
import uuid
from typing import Literal
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import text

from app.core.tenant import AuthenticatedContext, get_current_user
from app.schemas.transaction import MonthlySummaryOut, TransactionCreate, TransactionOut
from app.services.analytics_service import get_monthly_summary

router = APIRouter()


@router.get("/", response_model=list[TransactionOut])
async def list_transactions(
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    kind: Literal["DEBIT", "CREDIT"] | None = None,
    category: str | None = None,
    ctx: AuthenticatedContext = Depends(get_current_user)
):
    """Retrieve user transactions ledger with optional filters and pagination."""
    query_str = """
        SELECT id, account_id, client_id, amount_minor, currency, kind,
               category, payment_mode, description, occurred_on, created_at
        FROM transactions
        WHERE user_id = :u
    """
    params: dict = {"u": ctx.user_id, "limit": limit, "offset": offset}
    
    if kind:
        query_str += " AND kind = :kind"
        params["kind"] = kind
    if category:
        query_str += " AND LOWER(category) = LOWER(:category)"
        params["category"] = category.strip()
        
    query_str += " ORDER BY occurred_on DESC, created_at DESC LIMIT :limit OFFSET :offset"
    
    res = await ctx.session.execute(text(query_str), params)
    return [TransactionOut(**dict(r._mapping)) for r in res.all()]


@router.post("/", response_model=TransactionOut, status_code=status.HTTP_201_CREATED)
async def create_transaction(payload: TransactionCreate, ctx: AuthenticatedContext = Depends(get_current_user)):
    """
    Record an income or expense transaction.
    Guarantees idempotency via `client_id` (offline sync protection).
    Automatically updates account balance if `account_id` is supplied.
    """
    txn_id = uuid.uuid4()
    cat_normalized = payload.category.strip().lower()

    # Insert transaction with conflict prevention on (user_id, client_id)
    res = await ctx.session.execute(
        text("""
            INSERT INTO transactions (
                id, tenant_id, user_id, account_id, client_id, amount_minor,
                kind, category, payment_mode, description, occurred_on
            )
            VALUES (
                :id, :t, :u, :acc, :cid, :amt,
                :kind, :cat, :pm, :desc, :dt
            )
            ON CONFLICT (user_id, client_id) DO NOTHING
            RETURNING id, account_id, client_id, amount_minor, currency, kind,
                      category, payment_mode, description, occurred_on, created_at
        """),
        {
            "id": txn_id,
            "t": ctx.tenant_id,
            "u": ctx.user_id,
            "acc": payload.account_id,
            "cid": payload.client_id,
            "amt": payload.amount_minor,
            "kind": payload.kind,
            "cat": cat_normalized,
            "pm": payload.payment_mode,
            "desc": payload.description.strip(),
            "dt": payload.occurred_on
        }
    )
    row = res.first()
    
    # If duplicate client_id was submitted, fetch and return existing transaction
    if not row:
        existing_res = await ctx.session.execute(
            text("""
                SELECT id, account_id, client_id, amount_minor, currency, kind,
                       category, payment_mode, description, occurred_on, created_at
                FROM transactions
                WHERE user_id = :u AND client_id = :cid
            """),
            {"u": ctx.user_id, "cid": payload.client_id}
        )
        existing_row = existing_res.first()
        if existing_row:
            return TransactionOut(**dict(existing_row._mapping))
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Failed to record transaction.")

    # Update account balance if account_id is bound
    if payload.account_id:
        balance_change = payload.amount_minor if payload.kind == "CREDIT" else -payload.amount_minor
        await ctx.session.execute(
            text("""
                UPDATE accounts
                SET balance_minor = balance_minor + :delta, updated_at = now()
                WHERE id = :acc AND user_id = :u
            """),
            {"delta": balance_change, "acc": payload.account_id, "u": ctx.user_id}
        )

    return TransactionOut(**dict(row._mapping))


@router.delete("/{txn_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_transaction(txn_id: uuid.UUID, ctx: AuthenticatedContext = Depends(get_current_user)):
    """Delete a transaction and reverse balance from bound account."""
    fetch_res = await ctx.session.execute(
        text("SELECT account_id, amount_minor, kind FROM transactions WHERE id = :id AND user_id = :u"),
        {"id": txn_id, "u": ctx.user_id}
    )
    row = fetch_res.first()
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transaction not found.")

    if row.account_id:
        # Reverse balance change
        reverse_delta = -row.amount_minor if row.kind == "CREDIT" else row.amount_minor
        await ctx.session.execute(
            text("UPDATE accounts SET balance_minor = balance_minor + :delta WHERE id = :acc AND user_id = :u"),
            {"delta": reverse_delta, "acc": row.account_id, "u": ctx.user_id}
        )

    await ctx.session.execute(
        text("DELETE FROM transactions WHERE id = :id AND user_id = :u"),
        {"id": txn_id, "u": ctx.user_id}
    )


@router.get("/summary", response_model=MonthlySummaryOut)
async def monthly_summary(
    month: str | None = Query(default=None, pattern=r"^\d{4}-\d{2}$", description="YYYY-MM"),
    ctx: AuthenticatedContext = Depends(get_current_user)
):
    """Retrieve full cashflow breakdown and category expense distribution for the month."""
    return await get_monthly_summary(ctx.session, ctx.user_id, month)

