from fastapi import APIRouter

from app.api.v1.endpoints import (
    accounts,
    admin,
    ai_assistant,
    auth,
    budgets,
    calculators,
    consents,
    goals,
    learning,
    profiles,
    schemes,
    transactions,
)

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["Authentication & Identity"])
api_router.include_router(profiles.router, prefix="/profiles", tags=["Demographics & DPDP"])
api_router.include_router(accounts.router, prefix="/accounts", tags=["Financial Accounts"])
api_router.include_router(transactions.router, prefix="/transactions", tags=["Ledger & Transactions"])
api_router.include_router(budgets.router, prefix="/budgets", tags=["Budgets & Alerts"])
api_router.include_router(goals.router, prefix="/goals", tags=["Savings Goals"])
api_router.include_router(schemes.router, prefix="/schemes", tags=["Government Schemes & Eligibility"])
api_router.include_router(ai_assistant.router, prefix="/ai", tags=["FinSmart AI Assistant"])
api_router.include_router(calculators.router, prefix="/calc", tags=["Financial Calculators"])
api_router.include_router(learning.router, prefix="/learning", tags=["Financial Literacy & Fraud Shield"])
api_router.include_router(consents.router, prefix="/consents", tags=["DPDP 2023 Consent Ledger"])
api_router.include_router(admin.router, prefix="/admin", tags=["Institution Admin Console"])

