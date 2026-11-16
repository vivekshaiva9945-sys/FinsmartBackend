import os
import unittest
from decimal import Decimal

os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://x:y@localhost/z")
os.environ.setdefault("JWT_SECRET", "x" * 32)

from app.core import emi, evaluate, to_paise


class TestCoreLegacy(unittest.TestCase):
    def test_emi(self):
        self.assertEqual(emi(Decimal(100000), Decimal(12), 12), Decimal("8884.88"))

    def test_paise(self):
        self.assertEqual(to_paise(Decimal("100.50")), 10050)

    def test_rules(self):
        rule = {"all": [{"field": "age", "op": "between", "value": [18, 40], "label": "Age 18-40"}]}
        self.assertTrue(evaluate(rule, {"age": 25})["eligible"])
        self.assertFalse(evaluate(rule, {"age": 50})["eligible"])
        self.assertFalse(evaluate(rule, {})["eligible"])


if __name__ == "__main__":
    unittest.main()
