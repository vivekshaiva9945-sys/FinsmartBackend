import unittest
import uuid
from decimal import Decimal
from fastapi import HTTPException
from pydantic import ValidationError

from app.api.v1.endpoints.admin import get_institution_stats
from app.api.v1.endpoints.calculators import (
    compound_endpoint,
    emergency_fund_endpoint,
    emi_endpoint,
    sip_endpoint,
)
from app.core.tenant import AuthenticatedContext
from app.schemas.auth import UserLogin, UserRegister
from app.schemas.budget import BudgetCreate
from app.schemas.calculator import EMICalculatorIn, EmergencyFundIn, SIPCalculatorIn
from app.schemas.goal import GoalCreate
from app.schemas.transaction import TransactionCreate


def run_sync(coro):
    """Executes a coroutine that completes synchronously without event loop overhead."""
    try:
        coro.send(None)
    except StopIteration as e:
        return e.value


class TestApiEndpoints(unittest.TestCase):
    # -------------------------------------------------------------------------
    # 1. Calculator Endpoints
    # -------------------------------------------------------------------------
    def test_emi_calculator_endpoint(self):
        """Test loan EMI calculation endpoint returns rounded banker's values."""
        payload = EMICalculatorIn(principal=Decimal(100000), annual_rate=Decimal(12), months=12)
        res = run_sync(emi_endpoint(payload))
        self.assertEqual(res["monthly_emi"], "8884.88")
        self.assertEqual(res["total_payable"], "106618.56")
        self.assertEqual(res["total_interest"], "6618.56")

    def test_sip_calculator_endpoint(self):
        """Test SIP wealth generation calculation endpoint."""
        payload = SIPCalculatorIn(monthly=Decimal(5000), annual_rate=Decimal(12), months=12)
        res = run_sync(sip_endpoint(payload))
        self.assertEqual(res["total_invested"], "60000.00")
        self.assertTrue(Decimal(res["future_value"]) > Decimal("60000.00"))
        self.assertTrue(Decimal(res["wealth_gain"]) > Decimal("0.00"))

    def test_emergency_fund_calculator_endpoint(self):
        """Test emergency fund calculation endpoint."""
        payload = EmergencyFundIn(monthly_expenses=Decimal(25000), target_months=6)
        res = run_sync(emergency_fund_endpoint(payload))
        self.assertEqual(res["recommended_fund"], "150000.00")
        self.assertEqual(res["minimum_safe_fund"], "75000.00")

    # -------------------------------------------------------------------------
    # 2. Schema Validation & Negative Boundary Tests
    # -------------------------------------------------------------------------
    def test_calculator_negative_inputs(self):
        """Verify negative and zero numbers are rejected by calculator schemas."""
        with self.assertRaises(ValidationError):
            EMICalculatorIn(principal=Decimal(-100), annual_rate=Decimal(10), months=12)

        with self.assertRaises(ValidationError):
            EMICalculatorIn(principal=Decimal(1000), annual_rate=Decimal(10), months=0)

        with self.assertRaises(ValidationError):
            SIPCalculatorIn(monthly=Decimal(0), annual_rate=Decimal(10), months=12)

        with self.assertRaises(ValidationError):
            EmergencyFundIn(monthly_expenses=Decimal(-500), target_months=6)

    def test_transaction_negative_amount_validation(self):
        """Verify negative or zero monetary amounts are rejected for transactions."""
        with self.assertRaises(ValidationError):
            TransactionCreate(amount_minor=0, kind="DEBIT", category="food")

        with self.assertRaises(ValidationError):
            TransactionCreate(amount_minor=-5000, kind="DEBIT", category="food")

        # Valid transaction creation
        valid_txn = TransactionCreate(amount_minor=15000, kind="DEBIT", category="food", description="Groceries")
        self.assertEqual(valid_txn.amount_minor, 15000)
        self.assertEqual(valid_txn.kind, "DEBIT")

    def test_budget_negative_limit_validation(self):
        """Verify negative or zero budget limits are rejected."""
        with self.assertRaises(ValidationError):
            BudgetCreate(category="food", limit_minor=0)

        with self.assertRaises(ValidationError):
            BudgetCreate(category="food", limit_minor=-1000)

        valid_b = BudgetCreate(category="food", limit_minor=500000)
        self.assertEqual(valid_b.limit_minor, 500000)

    def test_goal_target_validation(self):
        """Verify savings goal target must be greater than zero."""
        with self.assertRaises(ValidationError):
            GoalCreate(name="Trip", target_minor=0)

        with self.assertRaises(ValidationError):
            GoalCreate(name="Trip", target_minor=-5000)

        valid_g = GoalCreate(name="Emergency Buffer", target_minor=2000000)
        self.assertEqual(valid_g.target_minor, 2000000)

    def test_user_registration_validation(self):
        """Verify user registration rejects missing consent, invalid emails, and short passwords."""
        # Missing explicit DPDP consent
        with self.assertRaises(ValidationError):
            UserRegister(
                email="user@vtu.ac.in",
                password="ShortPassword123!",
                full_name="User Test",
                consent_data_processing=False  # Required True by law
            )

        # Password < 8 characters
        with self.assertRaises(ValidationError):
            UserRegister(
                email="user@vtu.ac.in",
                password="123",
                full_name="User Test",
                consent_data_processing=True
            )

        # Invalid email format
        with self.assertRaises(ValidationError):
            UserRegister(
                email="not-an-email",
                password="StrongPassword123!",
                full_name="User Test",
                consent_data_processing=True
            )

    # -------------------------------------------------------------------------
    # 3. Role-Based Permissions & Admin Protection
    # -------------------------------------------------------------------------
    def test_admin_endpoint_forbidden_for_non_admins(self):
        """Verify non-admin roles (student, faculty) receive 403 Forbidden on /admin/stats."""
        student_ctx = AuthenticatedContext(
            session=None,  # type: ignore
            tenant_id=uuid.uuid4(),
            user_id=uuid.uuid4(),
            role="student",
            email="student@vtu.ac.in",
            full_name="Student Test"
        )
        with self.assertRaises(HTTPException) as cm:
            run_sync(get_institution_stats(student_ctx))
        self.assertEqual(cm.exception.status_code, 403)

        faculty_ctx = AuthenticatedContext(
            session=None,  # type: ignore
            tenant_id=uuid.uuid4(),
            user_id=uuid.uuid4(),
            role="faculty",
            email="prof@vtu.ac.in",
            full_name="Prof Test"
        )
        with self.assertRaises(HTTPException) as cm_fac:
            run_sync(get_institution_stats(faculty_ctx))
        self.assertEqual(cm_fac.exception.status_code, 403)


if __name__ == "__main__":
    unittest.main()
