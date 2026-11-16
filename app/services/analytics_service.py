import datetime as dt
import uuid
from typing import Any
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.budget import BudgetStatusOut
from app.schemas.transaction import CategoryBreakdown, MonthlySummaryOut


async def get_monthly_summary(session: AsyncSession, user_id: uuid.UUID, month_str: str | None = None) -> MonthlySummaryOut:
    """Computes comprehensive monthly cashflow summary and category distribution."""
    if not month_str:
        month_str = dt.date.today().strftime("%Y-%m")
        
    start_date = dt.date.fromisoformat(f"{month_str}-01")
    # Determine first day of next month
    if start_date.month == 12:
        end_date = dt.date(start_date.year + 1, 1, 1)
    else:
        end_date = dt.date(start_date.year, start_date.month + 1, 1)
        
    res = await session.execute(
        text("""
            SELECT kind, category, SUM(amount_minor)::bigint AS total_minor, COUNT(*)::int AS txn_count
            FROM transactions
            WHERE user_id = :u AND occurred_on >= :start AND occurred_on < :end
            GROUP BY kind, category
            ORDER BY total_minor DESC
        """),
        {"u": user_id, "start": start_date, "end": end_date}
    )
    rows = [dict(r._mapping) for r in res.all()]
    
    total_income = sum(r["total_minor"] for r in rows if r["kind"] == "CREDIT")
    total_expense = sum(r["total_minor"] for r in rows if r["kind"] == "DEBIT")
    balance = total_income - total_expense
    
    savings_rate = 0.0
    if total_income > 0:
        savings_rate = round(max(0.0, float(balance) / float(total_income) * 100.0), 1)

    by_category: list[CategoryBreakdown] = []
    expense_rows = [r for r in rows if r["kind"] == "DEBIT"]
    
    for r in expense_rows:
        pct = round((float(r["total_minor"]) / float(total_expense) * 100.0), 1) if total_expense > 0 else 0.0
        by_category.append(
            CategoryBreakdown(
                category=r["category"],
                kind=r["kind"],
                total_minor=r["total_minor"],
                count=r["txn_count"],
                percentage=pct
            )
        )

    return MonthlySummaryOut(
        month=month_str,
        income_minor=total_income,
        expense_minor=total_expense,
        balance_minor=balance,
        savings_rate_pct=savings_rate,
        by_category=by_category
    )


async def get_budget_statuses(session: AsyncSession, user_id: uuid.UUID) -> list[BudgetStatusOut]:
    """Evaluates user budgets against current month expenses and computes utilization levels."""
    start_date = dt.date.today().replace(day=1)
    
    res = await session.execute(
        text("""
            SELECT 
                b.category,
                b.limit_minor,
                b.period,
                COALESCE(SUM(t.amount_minor), 0)::bigint AS spent_minor
            FROM budgets b
            LEFT JOIN transactions t 
                ON t.user_id = b.user_id 
                AND LOWER(t.category) = LOWER(b.category)
                AND t.kind = 'DEBIT'
                AND t.occurred_on >= :start_date
            WHERE b.user_id = :u
            GROUP BY b.category, b.limit_minor, b.period
            ORDER BY b.category ASC
        """),
        {"u": user_id, "start_date": start_date}
    )
    rows = [dict(r._mapping) for r in res.all()]
    
    output: list[BudgetStatusOut] = []
    for r in rows:
        limit = r["limit_minor"]
        spent = r["spent_minor"]
        pct = int(spent * 100 // limit) if limit > 0 else 0
        rem = max(0, limit - spent)
        
        if pct >= 100:
            level = "over"
        elif pct >= 80:
            level = "warning"
        else:
            level = "ok"
            
        output.append(
            BudgetStatusOut(
                category=r["category"],
                limit_minor=limit,
                spent_minor=spent,
                remaining_minor=rem,
                percent=pct,
                level=level,
                period=r["period"]
            )
        )
    return output

