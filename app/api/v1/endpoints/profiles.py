import datetime as dt
import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import text

from app.core.tenant import AuthenticatedContext, get_current_user
from app.schemas.consent import DSARDataExport
from app.schemas.profile import UserProfileIn, UserProfileOut

router = APIRouter()


@router.get("", response_model=UserProfileOut | None, include_in_schema=False)
@router.get("/", response_model=UserProfileOut | None)
async def get_profile(ctx: AuthenticatedContext = Depends(get_current_user)):
    """Fetch user demographic profile used for automated welfare and scholarship scheme matching."""
    res = await ctx.session.execute(
        text("""
            SELECT id, tenant_id, user_id, age, gender, state, district, is_student,
                   academic_year, department, annual_family_income_minor, social_category,
                   has_bank_account, has_disability, ration_card_type, updated_at
            FROM user_profiles
            WHERE user_id = :u
        """),
        {"u": ctx.user_id}
    )
    row = res.first()
    if not row:
        return None
    return UserProfileOut(**dict(row._mapping))


@router.put("", response_model=UserProfileOut, include_in_schema=False)
@router.put("/", response_model=UserProfileOut)
async def update_profile(payload: UserProfileIn, ctx: AuthenticatedContext = Depends(get_current_user)):
    """Create or update user demographic profile."""
    res = await ctx.session.execute(
        text("""
            INSERT INTO user_profiles (
                tenant_id, user_id, age, gender, state, district, is_student,
                academic_year, department, annual_family_income_minor, social_category,
                has_bank_account, has_disability, ration_card_type, updated_at
            )
            VALUES (
                :t, :u, :age, :gender, :state, :district, :is_student,
                :academic_year, :department, :income, :cat,
                :bank, :disability, :ration, now()
            )
            ON CONFLICT (user_id) DO UPDATE SET
                age = EXCLUDED.age,
                gender = EXCLUDED.gender,
                state = EXCLUDED.state,
                district = EXCLUDED.district,
                is_student = EXCLUDED.is_student,
                academic_year = EXCLUDED.academic_year,
                department = EXCLUDED.department,
                annual_family_income_minor = EXCLUDED.annual_family_income_minor,
                social_category = EXCLUDED.social_category,
                has_bank_account = EXCLUDED.has_bank_account,
                has_disability = EXCLUDED.has_disability,
                ration_card_type = EXCLUDED.ration_card_type,
                updated_at = now()
            RETURNING id, tenant_id, user_id, age, gender, state, district, is_student,
                      academic_year, department, annual_family_income_minor, social_category,
                      has_bank_account, has_disability, ration_card_type, updated_at
        """),
        {
            "t": ctx.tenant_id,
            "u": ctx.user_id,
            "age": payload.age,
            "gender": payload.gender,
            "state": payload.state,
            "district": payload.district,
            "is_student": payload.is_student,
            "academic_year": payload.academic_year,
            "department": payload.department,
            "income": payload.annual_family_income_minor,
            "cat": payload.social_category,
            "bank": payload.has_bank_account,
            "disability": payload.has_disability,
            "ration": payload.ration_card_type,
        }
    )
    row = res.one()
    return UserProfileOut(**dict(row._mapping))


@router.get("/dsar-export", response_model=DSARDataExport)
async def export_my_data(ctx: AuthenticatedContext = Depends(get_current_user)):
    """
    DPDP Act 2023 - Right to Data Portability (DSAR).
    Exports complete user data ledger in structured JSON format.
    """
    # 1. User
    u_res = await ctx.session.execute(
        text("SELECT id, email, full_name, phone_number, role, created_at FROM users WHERE id = :u"),
        {"u": ctx.user_id}
    )
    user_data = dict(u_res.one()._mapping)
    user_data["id"] = str(user_data["id"])
    user_data["created_at"] = user_data["created_at"].isoformat()

    # 2. Profile
    p_res = await ctx.session.execute(
        text("SELECT * FROM user_profiles WHERE user_id = :u"),
        {"u": ctx.user_id}
    )
    p_row = p_res.first()
    profile_data = None
    if p_row:
        profile_data = dict(p_row._mapping)
        profile_data["id"] = str(profile_data["id"])
        profile_data["user_id"] = str(profile_data["user_id"])
        profile_data["tenant_id"] = str(profile_data["tenant_id"])
        profile_data["updated_at"] = profile_data["updated_at"].isoformat()

    # 3. Accounts
    acc_res = await ctx.session.execute(
        text("SELECT id, name, account_type, balance_minor, currency FROM accounts WHERE user_id = :u"),
        {"u": ctx.user_id}
    )
    accounts = [dict(r._mapping) for r in acc_res.all()]
    for a in accounts:
        a["id"] = str(a["id"])

    # 4. Transactions
    tx_res = await ctx.session.execute(
        text("""
            SELECT id, amount_minor, currency, kind, category, payment_mode, description, occurred_on, created_at
            FROM transactions WHERE user_id = :u ORDER BY occurred_on DESC
        """),
        {"u": ctx.user_id}
    )
    txns = [dict(r._mapping) for r in tx_res.all()]
    for t in txns:
        t["id"] = str(t["id"])
        t["occurred_on"] = t["occurred_on"].isoformat()
        t["created_at"] = t["created_at"].isoformat()

    # 5. Budgets
    b_res = await ctx.session.execute(
        text("SELECT id, category, limit_minor, period FROM budgets WHERE user_id = :u"),
        {"u": ctx.user_id}
    )
    budgets = [dict(r._mapping) for r in b_res.all()]
    for b in budgets:
        b["id"] = str(b["id"])

    # 6. Goals
    g_res = await ctx.session.execute(
        text("SELECT id, name, target_minor, saved_minor, target_date, category, is_completed FROM goals WHERE user_id = :u"),
        {"u": ctx.user_id}
    )
    goals = [dict(r._mapping) for r in g_res.all()]
    for g in goals:
        g["id"] = str(g["id"])
        if g["target_date"]:
            g["target_date"] = g["target_date"].isoformat()

    # 7. Consents
    c_res = await ctx.session.execute(
        text("SELECT id, purpose, granted, at FROM consents WHERE user_id = :u"),
        {"u": ctx.user_id}
    )
    consents = [dict(r._mapping) for r in c_res.all()]
    for c in consents:
        c["id"] = str(c["id"])
        c["at"] = c["at"].isoformat()

    return DSARDataExport(
        user=user_data,
        profile=profile_data,
        accounts=accounts,
        transactions=txns,
        budgets=budgets,
        goals=goals,
        consents=consents,
        exported_at=dt.datetime.now(dt.timezone.utc)
    )


@router.delete("/erasure", status_code=status.HTTP_204_NO_CONTENT)
async def request_data_erasure(ctx: AuthenticatedContext = Depends(get_current_user)):
    """
    DPDP Act 2023 - Right to be Forgotten.
    Permanently deletes all financial transactions, profiles, budgets, and user credentials.
    """
    await ctx.session.execute(
        text("DELETE FROM users WHERE id = :u AND tenant_id = :t"),
        {"u": ctx.user_id, "t": ctx.tenant_id}
    )

