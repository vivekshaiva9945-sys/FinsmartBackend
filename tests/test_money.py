import unittest
from decimal import Decimal
from app.core.money import (
    calculate_compound_interest,
    calculate_emergency_fund,
    calculate_emi,
    calculate_sip,
    format_inr,
    to_paise,
    to_rupees,
)


class TestMoneyMath(unittest.TestCase):
    def test_to_paise_conversion(self):
        self.assertEqual(to_paise(Decimal("100.50")), 10050)
        self.assertEqual(to_paise("49.99"), 4999)
        self.assertEqual(to_paise(150), 15000)
        self.assertEqual(to_paise(0.05), 5)

    def test_to_rupees_conversion(self):
        self.assertEqual(to_rupees(10050), Decimal("100.50"))
        self.assertEqual(to_rupees(5), Decimal("0.05"))

    def test_format_inr(self):
        self.assertEqual(format_inr(10000000), "₹1,00,000.00")
        self.assertEqual(format_inr(25050), "₹250.50")

    def test_calculate_emi(self):
        # Principal 1,00,000 @ 12% p.a. for 12 months
        res = calculate_emi(Decimal(100000), Decimal(12), 12)
        self.assertEqual(res["monthly_emi"], "8884.88")
        self.assertEqual(res["total_payable"], "106618.56")
        self.assertEqual(res["total_interest"], "6618.56")

    def test_calculate_sip(self):
        # Monthly 5,000 @ 12% p.a. for 12 months
        res = calculate_sip(Decimal(5000), Decimal(12), 12)
        self.assertEqual(res["total_invested"], "60000.00")
        self.assertTrue(Decimal(res["future_value"]) > Decimal(60000))
        self.assertTrue(Decimal(res["wealth_gain"]) > Decimal(0))

    def test_calculate_emergency_fund(self):
        res = calculate_emergency_fund(Decimal(20000), 6)
        self.assertEqual(res["recommended_fund"], "120000.00")
        self.assertEqual(res["minimum_safe_fund"], "60000.00")

    def test_calculate_compound_interest(self):
        res = calculate_compound_interest(Decimal(10000), Decimal(10), Decimal(2), 1)
        self.assertEqual(res["final_amount"], "12100.00")
        self.assertEqual(res["interest_earned"], "2100.00")


if __name__ == "__main__":
    unittest.main()

