import unittest
from app.services.rules_engine import evaluate_condition, evaluate_scheme_rules


class TestRulesEngine(unittest.TestCase):
    def test_single_condition_operators(self):
        # gte
        cond_gte = {"field": "age", "op": "gte", "value": 18, "label": "Adult 18+"}
        self.assertTrue(evaluate_condition(cond_gte, {"age": 18})[0])
        self.assertTrue(evaluate_condition(cond_gte, {"age": 25})[0])
        self.assertFalse(evaluate_condition(cond_gte, {"age": 16})[0])

        # lte
        cond_lte = {"field": "income", "op": "lte", "value": 250000, "label": "Income <= 2.5L"}
        self.assertTrue(evaluate_condition(cond_lte, {"income": 200000})[0])
        self.assertFalse(evaluate_condition(cond_lte, {"income": 300000})[0])

        # between
        cond_between = {"field": "age", "op": "between", "value": [18, 40], "label": "Age 18 to 40"}
        self.assertTrue(evaluate_condition(cond_between, {"age": 18})[0])
        self.assertTrue(evaluate_condition(cond_between, {"age": 30})[0])
        self.assertTrue(evaluate_condition(cond_between, {"age": 40})[0])
        self.assertFalse(evaluate_condition(cond_between, {"age": 17})[0])
        self.assertFalse(evaluate_condition(cond_between, {"age": 41})[0])

        # in
        cond_in = {"field": "category", "op": "in", "value": ["SC", "ST", "OBC"], "label": "Reserved category"}
        self.assertTrue(evaluate_condition(cond_in, {"category": "OBC"})[0])
        self.assertFalse(evaluate_condition(cond_in, {"category": "GEN"})[0])

        # eq
        cond_eq = {"field": "is_student", "op": "eq", "value": True, "label": "Enrolled student"}
        self.assertTrue(evaluate_condition(cond_eq, {"is_student": True})[0])
        self.assertFalse(evaluate_condition(cond_eq, {"is_student": False})[0])

    def test_missing_field_handling(self):
        cond = {"field": "annual_income", "op": "lte", "value": 250000, "label": "Income limit"}
        is_met, msg = evaluate_condition(cond, {})
        self.assertFalse(is_met)
        self.assertIn("Information needed", msg)

    def test_multi_condition_scheme_evaluation(self):
        rule = {
            "all": [
                {"field": "is_student", "op": "eq", "value": True, "label": "Enrolled student"},
                {"field": "annual_family_income", "op": "lte", "value": 250000, "label": "Family income ceiling"},
                {"field": "social_category", "op": "in", "value": ["SC", "ST", "OBC"], "label": "Category SC/ST/OBC"}
            ]
        }
        
        eligible_profile = {
            "is_student": True,
            "annual_family_income": 180000,
            "social_category": "OBC"
        }
        res_eligible = evaluate_scheme_rules(rule, eligible_profile)
        self.assertTrue(res_eligible["eligible"])
        self.assertEqual(res_eligible["matched_conditions"], 3)
        self.assertEqual(res_eligible["total_conditions"], 3)

        ineligible_profile = {
            "is_student": True,
            "annual_family_income": 400000,
            "social_category": "GEN"
        }
        res_ineligible = evaluate_scheme_rules(rule, ineligible_profile)
        self.assertFalse(res_ineligible["eligible"])
        self.assertEqual(res_ineligible["matched_conditions"], 1)


if __name__ == "__main__":
    unittest.main()

