from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import text

from app.core.tenant import AuthenticatedContext, get_current_user
from app.schemas.admin import AdminStatsOut

router = APIRouter()


@router.get("/stats", response_model=AdminStatsOut)
async def get_institution_stats(ctx: AuthenticatedContext = Depends(get_current_user)):
    """
    College/Institution Administrator overview.
    Provides aggregated anonymized participation metrics with zero individual student PII.
    Requires role 'college_admin' or 'admin'.
    """
    if ctx.role not in ("college_admin", "admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access restricted to College Administrators and Platform Admins."
        )

    res = await ctx.session.execute(
        text("""
            SELECT 
                (SELECT count(*)::int FROM users WHERE tenant_id = :t) AS total_users,
                (SELECT count(*)::int FROM transactions WHERE tenant_id = :t) AS total_txns,
                (SELECT COALESCE(SUM(amount_minor), 0)::bigint FROM transactions WHERE tenant_id = :t) AS total_vol,
                (SELECT count(*)::int FROM goals WHERE tenant_id = :t) AS total_goals,
                (SELECT count(*)::int FROM budgets WHERE tenant_id = :t) AS total_budgets,
                (SELECT name FROM tenants WHERE id = :t) AS tenant_name,
                (SELECT slug FROM tenants WHERE id = :t) AS tenant_slug
        """),
        {"t": ctx.tenant_id}
    )
    row = res.one()

    return AdminStatsOut(
        tenant_name=row.tenant_name,
        tenant_slug=row.tenant_slug,
        total_users=row.total_users,
        total_transactions=row.total_txns,
        total_volume_minor=row.total_vol,
        total_goals=row.total_goals,
        total_active_budgets=row.total_budgets
    )

