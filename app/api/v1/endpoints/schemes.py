from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import text

from app.core.tenant import TenantContext, get_tenant_db
from app.schemas.scheme import ProfileEvaluationRequest, SchemeEvaluationResult, SchemeOut
from app.services.rules_engine import evaluate_scheme_rules

router = APIRouter()


@router.get("/", response_model=list[SchemeOut])
async def list_schemes(tenant: TenantContext = Depends(get_tenant_db)):
    """List all verified Central and State welfare and scholarship schemes."""
    res = await tenant.session.execute(
        text("""
            SELECT code, title_en, title_kn, title_hi, agency, category,
                   summary, benefits, source_url, documents_required,
                   application_steps, last_verified_at
            FROM schemes
            ORDER BY category ASC, code ASC
        """)
    )
    return [SchemeOut(**dict(r._mapping)) for r in res.all()]


@router.get("/{code}", response_model=SchemeOut)
async def get_scheme_by_code(code: str, tenant: TenantContext = Depends(get_tenant_db)):
    """Fetch complete details, document checklist, and step-by-step guide for a specific scheme."""
    res = await tenant.session.execute(
        text("""
            SELECT code, title_en, title_kn, title_hi, agency, category,
                   summary, benefits, source_url, documents_required,
                   application_steps, last_verified_at
            FROM schemes
            WHERE code = :code
        """),
        {"code": code.upper().strip()}
    )
    row = res.first()
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Scheme '{code}' not found.")
    return SchemeOut(**dict(row._mapping))


@router.post("/eligibility", response_model=list[SchemeEvaluationResult])
async def evaluate_eligibility(payload: ProfileEvaluationRequest, tenant: TenantContext = Depends(get_tenant_db)):
    """
    Evaluates applicant profile criteria deterministically against all curated schemes using
    the pure declarative JSON rule engine. Returns explainable 'Why eligible' and 'Why not eligible' clauses.
    """
    res = await tenant.session.execute(
        text("""
            SELECT code, title_en, title_kn, title_hi, agency, category,
                   summary, benefits, source_url, documents_required,
                   application_steps, last_verified_at, rule
            FROM schemes
        """)
    )
    all_schemes = [dict(r._mapping) for r in res.all()]
    profile_dict = payload.model_dump()

    evaluated_results: list[SchemeEvaluationResult] = []

    for s in all_schemes:
        rule = s.pop("rule")
        eval_meta = evaluate_scheme_rules(rule, profile_dict)
        
        evaluated_results.append(
            SchemeEvaluationResult(
                code=s["code"],
                title_en=s["title_en"],
                title_kn=s["title_kn"],
                title_hi=s["title_hi"],
                agency=s["agency"],
                category=s["category"],
                summary=s["summary"],
                benefits=s["benefits"],
                source_url=s["source_url"],
                documents_required=s["documents_required"],
                application_steps=s["application_steps"],
                last_verified_at=s["last_verified_at"],
                eligible=eval_meta["eligible"],
                reasons=eval_meta["reasons"],
                matched_conditions=eval_meta["matched_conditions"],
                total_conditions=eval_meta["total_conditions"]
            )
        )

    # Sort so eligible schemes appear first
    evaluated_results.sort(key=lambda x: (not x.eligible, -x.matched_conditions))
    return evaluated_results

