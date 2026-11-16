from pydantic import BaseModel


class AdminStatsOut(BaseModel):
    tenant_name: str
    tenant_slug: str
    total_users: int
    total_transactions: int
    total_volume_minor: int
    total_goals: int
    total_active_budgets: int

