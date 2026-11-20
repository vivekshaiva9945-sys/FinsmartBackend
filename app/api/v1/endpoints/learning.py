from typing import Literal
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import text

from app.core.tenant import TenantContext, get_tenant_db
from app.schemas.learning import LearningModuleOut, QuizResultOut, QuizSubmitIn

router = APIRouter()


@router.get("", response_model=list[LearningModuleOut], include_in_schema=False)
@router.get("/", response_model=list[LearningModuleOut])
async def list_modules(
    lang: Literal["en", "kn", "hi"] = Query(default="en"),
    tenant: TenantContext = Depends(get_tenant_db)
):
    """Retrieve bite-sized financial literacy and digital safety modules in English, Kannada, or Hindi."""
    res = await tenant.session.execute(
        text("""
            SELECT id, lang, category, title, summary, body, quiz
            FROM learning_modules
            WHERE lang = :l
            ORDER BY id ASC
        """),
        {"l": lang}
    )
    return [LearningModuleOut(**dict(r._mapping)) for r in res.all()]


@router.post("/quiz/submit", response_model=QuizResultOut)
async def submit_quiz(payload: QuizSubmitIn, tenant: TenantContext = Depends(get_tenant_db)):
    """Evaluate interactive quiz answer and return instant explanation."""
    res = await tenant.session.execute(
        text("SELECT quiz FROM learning_modules WHERE id = :id"),
        {"id": payload.module_id}
    )
    row = res.first()
    if not row or not row.quiz:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Module quiz not found.")

    quiz_list = row.quiz
    if not quiz_list:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No quiz available for this module.")

    first_q = quiz_list[0]
    correct_idx = first_q.get("correct_index", 0)
    is_correct = payload.selected_option_index == correct_idx
    explanation = first_q.get("explanation", "")

    return QuizResultOut(
        is_correct=is_correct,
        correct_index=correct_idx,
        explanation=explanation
    )

