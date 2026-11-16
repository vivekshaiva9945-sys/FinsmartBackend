# app.core package initialization and backwards-compatibility re-exports
from app.core.config import settings
from app.core.database import AsyncSessionLocal as Session, engine, get_db
from app.core.money import (
    calculate_compound_interest as compound,
    calculate_emergency_fund,
    calculate_emi as emi_calc,
    calculate_sip as sip_calc,
    format_inr,
    to_paise,
    to_rupees,
)
from app.core.pii import contains_pii, scrub_pii
from app.core.security import create_access_token as make_token, hash_password as hash_pw, verify_password as verify_pw
from app.core.tenant import (
    AuthenticatedContext as Ctx,
    TenantContext as Tenant,
    get_current_user as current,
    get_tenant_db as tenant_db,
)
from app.services.rules_engine import evaluate_scheme_rules as evaluate


def emi(principal, annual_pct, months):
    res = emi_calc(principal, annual_pct, months)
    from decimal import Decimal
    return Decimal(res["monthly_emi"])


def sip_future_value(monthly, annual_pct, months):
    res = sip_calc(monthly, annual_pct, months)
    from decimal import Decimal
    return Decimal(res["future_value"])

