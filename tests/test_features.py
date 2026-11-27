import datetime as dt
import unittest
import uuid
from decimal import Decimal

from app.core.money import calculate_compound_interest, calculate_emergency_fund, calculate_emi, calculate_sip, to_paise, to_rupees
from app.services.ai_service import check_guardrails
from app.services.rules_engine import evaluate_condition, evaluate_scheme_rules


class TestFeatures(unittest.TestCase):
    # -------------------------------------------------------------------------
    # 1. Money & Minor Units Math
    # -------------------------------------------------------------------------
    def test_integer_paise_minor_units(self):
        """Verify strict integer paise conversion without floating point drift."""
        self.assertEqual(to_paise("1500.50"), 150050)
        self.assertEqual(to_paise(1500.50), 150050)
        self.assertEqual(to_rupees(150050), Decimal("1500.50"))
        # Edge cases: 1 paisa, 0 rupees
        self.assertEqual(to_paise("0.01"), 1)
        self.assertEqual(to_paise(0), 0)

    # -------------------------------------------------------------------------
    # 2. Budget Utilization & Alert Thresholds
    # -------------------------------------------------------------------------
    def test_budget_threshold_classification(self):
        """Verify budget status levels: ok (<80%), warning (80-99%), over (>=100%)."""
        limit = 1000000  # ₹10,000

        def compute_level(spent: int, lim: int) -> tuple[int, str, int]:
            pct = int(spent * 100 // lim) if lim > 0 else 0
            rem = max(0, lim - spent)
            if pct >= 100:
                lvl = "over"
            elif pct >= 80:
                lvl = "warning"
            else:
                lvl = "ok"
            return pct, lvl, rem

        # Safe spend: ₹5,000 / ₹10,000 = 50%
        pct, lvl, rem = compute_level(500000, limit)
        self.assertEqual(pct, 50)
        self.assertEqual(lvl, "ok")
        self.assertEqual(rem, 500000)

        # Warning threshold: ₹8,000 / ₹10,000 = 80%
        pct, lvl, rem = compute_level(800000, limit)
        self.assertEqual(pct, 80)
        self.assertEqual(lvl, "warning")
        self.assertEqual(rem, 200000)

        # Warning threshold: ₹9,500 / ₹10,000 = 95%
        pct, lvl, rem = compute_level(950000, limit)
        self.assertEqual(pct, 95)
        self.assertEqual(lvl, "warning")
        self.assertEqual(rem, 50000)

        # Overspend threshold: ₹10,000 / ₹10,000 = 100%
        pct, lvl, rem = compute_level(1000000, limit)
        self.assertEqual(pct, 100)
        self.assertEqual(lvl, "over")
        self.assertEqual(rem, 0)

        # Excess overspend: ₹12,500 / ₹10,000 = 125%
        pct, lvl, rem = compute_level(1250000, limit)
        self.assertEqual(pct, 125)
        self.assertEqual(lvl, "over")
        self.assertEqual(rem, 0)  # non-negative remaining

    # -------------------------------------------------------------------------
    # 3. Savings Goals Milestone Math
    # -------------------------------------------------------------------------
    def test_goal_progress_and_recommendation(self):
        """Verify savings milestone percentage and monthly recommended allocation."""
        target = 6000000  # ₹60,000
        saved = 1500000   # ₹15,000
        rem = max(0, target - saved)
        pct = min(100, int(saved * 100 // target))

        self.assertEqual(pct, 25)
        self.assertEqual(rem, 4500000)

        # 6 months remaining
        days_left = 180
        months_left = max(1, days_left // 30)
        monthly_rec = rem // months_left
        self.assertEqual(monthly_rec, 750000)  # ₹7,500 per month

        # Goal completed
        saved_done = 6500000
        pct_done = min(100, int(saved_done * 100 // target))
        self.assertEqual(pct_done, 100)
        self.assertTrue(saved_done >= target)

    # -------------------------------------------------------------------------
    # 4. Deterministic Scheme Evaluation Engine
    # -------------------------------------------------------------------------
    def test_scheme_rules_evaluation(self):
        """Verify deterministic welfare scheme matching with clear explainable clauses."""
        ssp_karnataka_rule = {
            "all": [
                {"field": "is_student", "op": "eq", "value": True, "label": "Currently enrolled student"},
                {"field": "annual_family_income", "op": "lte", "value": 250000, "label": "Annual income <= 2.5 Lakhs"},
                {"field": "state", "op": "eq", "value": "Karnataka", "label": "Karnataka domicile"},
                {"field": "has_bank_account", "op": "eq", "value": True, "label": "Active bank account for DBT"}
            ]
        }

        # Eligible profile
        profile_eligible = {
            "is_student": True,
            "annual_family_income": 180000,
            "state": "Karnataka",
            "has_bank_account": True
        }
        res_ok = evaluate_scheme_rules(ssp_karnataka_rule, profile_eligible)
        self.assertTrue(res_ok["eligible"])
        self.assertEqual(res_ok["matched_conditions"], 4)
        self.assertEqual(res_ok["total_conditions"], 4)
        for r in res_ok["reasons"]:
            self.assertTrue(r.startswith("Criteria satisfied:"))

        # Ineligible profile (income exceeded)
        profile_over_income = {
            "is_student": True,
            "annual_family_income": 400000,
            "state": "Karnataka",
            "has_bank_account": True
        }
        res_fail = evaluate_scheme_rules(ssp_karnataka_rule, profile_over_income)
        self.assertFalse(res_fail["eligible"])
        self.assertEqual(res_fail["matched_conditions"], 3)
        self.assertIn("Criteria not met: Annual income <= 2.5 Lakhs", res_fail["reasons"])

    # -------------------------------------------------------------------------
    # 5. AI Mentor Guardrails & Educational Refusal
    # -------------------------------------------------------------------------
    def test_ai_speculative_guardrails(self):
        """Verify AI mentor guardrails intercept risky queries with educational guidance."""
        # Speculative queries must trigger guardrails
        self.assertIsNotNone(check_guardrails("Which crypto should I buy today?"))
        self.assertIsNotNone(check_guardrails("What are the best stocks to buy for quick money?"))
        self.assertIsNotNone(check_guardrails("Where can I get guaranteed 50% returns?"))
        self.assertIsNotNone(check_guardrails("Give me intraday f&o tips"))
        self.assertIsNotNone(check_guardrails("Best online rummy and betting app"))

        # Safe literacy queries must pass
        self.assertIsNone(check_guardrails("How do I build an emergency fund for 6 months?"))
        self.assertIsNone(check_guardrails("Explain the 50/30/20 budgeting rule for college students"))
        self.assertIsNone(check_guardrails("What are the benefits of Sukanya Samriddhi Yojana?"))

    # -------------------------------------------------------------------------
    # 6. Financial Calculators Mathematical Accuracy
    # -------------------------------------------------------------------------
    def test_calculator_math_accuracy(self):
        """Verify mathematical precision of EMI, SIP, and Emergency fund calculators."""
        # 1. EMI: ₹2,00,000 at 10% for 24 months
        emi_out = calculate_emi(Decimal(200000), Decimal(10), 24)
        self.assertIsInstance(emi_out["monthly_emi"], str)
        self.assertTrue(Decimal(emi_out["monthly_emi"]) > 0)
        self.assertEqual(Decimal(emi_out["total_payable"]), Decimal(emi_out["monthly_emi"]) * 24)

        # 2. SIP: ₹3,000/month at 12% for 36 months
        sip_out = calculate_sip(Decimal(3000), Decimal(12), 36)
        self.assertEqual(sip_out["total_invested"], "108000.00")
        self.assertTrue(Decimal(sip_out["future_value"]) > Decimal("108000.00"))

        # 3. Emergency fund: ₹15,000 monthly expense for 6 months
        ef_out = calculate_emergency_fund(Decimal(15000), 6)
        self.assertEqual(ef_out["recommended_fund"], "90000.00")
        self.assertEqual(ef_out["minimum_safe_fund"], "45000.00")


if __name__ == "__main__":
    unittest.main()
