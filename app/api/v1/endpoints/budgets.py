import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import text

from app.core.tenant import AuthenticatedContext, get_current_user
from app.schemas.budget import BudgetCreate, BudgetOut, BudgetStatusOut
from app.services.analytics_service import get_budget_statuses

router = APIRouter()


@router.get("", response_model=list[BudgetOut], include_in_schema=False)
@router.get("/", response_model=list[BudgetOut])
async def list_budgets(ctx: AuthenticatedContext = Depends(get_current_user)):
    """List all configured category budgets for the current user."""
    res = await ctx.session.execute(
        text("SELECT id, category, limit_minor, period, created_at FROM budgets WHERE user_id = :u ORDER BY category ASC"),
        {"u": ctx.user_id}
    )
    return [BudgetOut(**dict(r._mapping)) for r in res.all()]


@router.put("", response_model=BudgetOut, include_in_schema=False)
@router.put("/", response_model=BudgetOut)
async def upsert_budget(payload: BudgetCreate, ctx: AuthenticatedContext = Depends(get_current_user)):
    """Set or update monthly budget limit for a specific category."""
    cat_normalized = payload.category.strip().lower()
    budget_id = uuid.uuid4()
    
    res = await ctx.session.execute(
        text("""
            INSERT INTO budgets (id, tenant_id, user_id, category, limit_minor, period)
            VALUES (:id, :t, :u, :cat, :limit, :period)
            ON CONFLICT (user_id, category, period) DO UPDATE
            SET limit_minor = EXCLUDED.limit_minor
            RETURNING id, category, limit_minor, period, created_at
        """),
        {
            "id": budget_id,
            "t": ctx.tenant_id,
            "u": ctx.user_id,
            "cat": cat_normalized,
            "limit": payload.limit_minor,
            "period": payload.period
        }
    )
    row = res.one()
    return BudgetOut(**dict(row._mapping))


@router.delete("/{budget_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_budget(budget_id: uuid.UUID, ctx: AuthenticatedContext = Depends(get_current_user)):
    """Remove a configured category budget."""
    res = await ctx.session.execute(
        text("DELETE FROM budgets WHERE id = :id AND user_id = :u"),
        {"id": budget_id, "u": ctx.user_id}
    )
    if res.rowcount == 0:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Budget not found.")
    return None


@router.get("/status", response_model=list[BudgetStatusOut])
async def get_status(ctx: AuthenticatedContext = Depends(get_current_user)):
    """Get active budget utilization status with warning (80%) and overspend (100%) thresholds."""
    return await get_budget_statuses(ctx.session, ctx.user_id)

