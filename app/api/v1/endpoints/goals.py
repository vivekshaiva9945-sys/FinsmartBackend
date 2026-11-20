import datetime as dt
import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import text

from app.core.tenant import AuthenticatedContext, get_current_user
from app.schemas.goal import GoalContribute, GoalCreate, GoalOut

router = APIRouter()


@router.get("", response_model=list[GoalOut], include_in_schema=False)
@router.get("/", response_model=list[GoalOut])
async def list_goals(ctx: AuthenticatedContext = Depends(get_current_user)):
    """List all savings goals with calculated progress, remaining amounts, and recommended monthly contributions."""
    res = await ctx.session.execute(
        text("""
            SELECT id, name, target_minor, saved_minor, target_date, category, is_completed, created_at
            FROM goals
            WHERE user_id = :u
            ORDER BY is_completed ASC, created_at DESC
        """),
        {"u": ctx.user_id}
    )
    goals_data = [dict(r._mapping) for r in res.all()]
    today = dt.date.today()
    output: list[GoalOut] = []

    for g in goals_data:
        target = g["target_minor"]
        saved = g["saved_minor"]
        rem = max(0, target - saved)
        pct = min(100, int(saved * 100 // target)) if target > 0 else 100
        
        monthly_rec = None
        if g["target_date"] and not g["is_completed"]:
            diff_days = (g["target_date"] - today).days
            if diff_days > 0:
                months_left = max(1, diff_days // 30)
                monthly_rec = rem // months_left

        output.append(
            GoalOut(
                id=g["id"],
                name=g["name"],
                target_minor=target,
                saved_minor=saved,
                remaining_minor=rem,
                percent=pct,
                target_date=g["target_date"],
                category=g["category"],
                is_completed=g["is_completed"] or (saved >= target),
                monthly_recommended_minor=monthly_rec,
                created_at=g["created_at"]
            )
        )
    return output


@router.post("", response_model=GoalOut, status_code=status.HTTP_201_CREATED, include_in_schema=False)
@router.post("/", response_model=GoalOut, status_code=status.HTTP_201_CREATED)
async def create_goal(payload: GoalCreate, ctx: AuthenticatedContext = Depends(get_current_user)):
    """Create a new savings goal."""
    goal_id = uuid.uuid4()
    res = await ctx.session.execute(
        text("""
            INSERT INTO goals (id, tenant_id, user_id, name, target_minor, target_date, category)
            VALUES (:id, :t, :u, :name, :target, :date, :cat)
            RETURNING id, name, target_minor, saved_minor, target_date, category, is_completed, created_at
        """),
        {
            "id": goal_id,
            "t": ctx.tenant_id,
            "u": ctx.user_id,
            "name": payload.name.strip(),
            "target": payload.target_minor,
            "date": payload.target_date,
            "cat": payload.category
        }
    )
    row = dict(res.one()._mapping)
    return GoalOut(
        id=row["id"],
        name=row["name"],
        target_minor=row["target_minor"],
        saved_minor=row["saved_minor"],
        remaining_minor=row["target_minor"] - row["saved_minor"],
        percent=0,
        target_date=row["target_date"],
        category=row["category"],
        is_completed=False,
        monthly_recommended_minor=None,
        created_at=row["created_at"]
    )


@router.post("/{goal_id}/contribute", response_model=GoalOut)
async def contribute_to_goal(goal_id: uuid.UUID, payload: GoalContribute, ctx: AuthenticatedContext = Depends(get_current_user)):
    """Deposit savings towards a goal."""
    res = await ctx.session.execute(
        text("""
            UPDATE goals
            SET saved_minor = saved_minor + :amt,
                is_completed = (saved_minor + :amt >= target_minor),
                updated_at = now()
            WHERE id = :id AND user_id = :u
            RETURNING id, name, target_minor, saved_minor, target_date, category, is_completed, created_at
        """),
        {"amt": payload.amount_minor, "id": goal_id, "u": ctx.user_id}
    )
    row = res.first()
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Goal not found.")

    r_dict = dict(row._mapping)
    target = r_dict["target_minor"]
    saved = r_dict["saved_minor"]
    rem = max(0, target - saved)
    pct = min(100, int(saved * 100 // target)) if target > 0 else 100

    return GoalOut(
        id=r_dict["id"],
        name=r_dict["name"],
        target_minor=target,
        saved_minor=saved,
        remaining_minor=rem,
        percent=pct,
        target_date=r_dict["target_date"],
        category=r_dict["category"],
        is_completed=r_dict["is_completed"],
        monthly_recommended_minor=None,
        created_at=r_dict["created_at"]
    )


@router.delete("/{goal_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_goal(goal_id: uuid.UUID, ctx: AuthenticatedContext = Depends(get_current_user)):
    """Delete a savings goal."""
    res = await ctx.session.execute(
        text("DELETE FROM goals WHERE id = :id AND user_id = :u"),
        {"id": goal_id, "u": ctx.user_id}
    )
    if res.rowcount == 0:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Goal not found.")
    return None

