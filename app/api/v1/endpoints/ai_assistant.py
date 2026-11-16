from fastapi import APIRouter, Depends
from app.core.tenant import TenantContext, get_tenant_db
from app.schemas.ai import AIChatRequest, AIChatResponse
from app.services.ai_service import answer_financial_query

router = APIRouter()


@router.post("/chat", response_model=AIChatResponse)
async def chat_with_assistant(payload: AIChatRequest, tenant: TenantContext = Depends(get_tenant_db)):
    """
    Interact with FinSmart AI Grounded Financial Literacy Assistant.
    - DPDP Act 2023 compliant: scrubs Aadhaar, PAN, and phone numbers before analysis.
    - Grounded in official RBI guidelines, welfare schemes, and financial education handbooks.
    - Strictly rejects speculative stock trading tips or get-rich schemes.
    """
    return await answer_financial_query(
        session=tenant.session,
        raw_message=payload.message,
        language=payload.language
    )

