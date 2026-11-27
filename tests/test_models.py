import unittest
import uuid
from datetime import date
from app.models import (
    Base,
    Tenant,
    User,
    UserProfile,
    Account,
    Transaction,
    Budget,
    Goal,
    Scheme,
    Consent,
    LearningModule,
    KnowledgeDoc,
)


class TestDeclarativeModels(unittest.TestCase):
    def test_model_tables_registered(self):
        table_names = Base.metadata.tables.keys()
        expected = [
            "tenants",
            "users",
            "user_profiles",
            "accounts",
            "transactions",
            "budgets",
            "goals",
            "consents",
            "schemes",
            "learning_modules",
            "knowledge_docs",
        ]
        for tbl in expected:
            self.assertIn(tbl, table_names, f"Table {tbl} not registered in Base.metadata")

    def test_tenant_model_instantiation(self):
        t = Tenant(slug="vtu_test", name="VTU Engineering College", subscription_tier="standard", is_active=True)
        self.assertEqual(t.slug, "vtu_test")
        self.assertEqual(t.subscription_tier, "standard")
        self.assertTrue(t.is_active)

    def test_user_and_profile_model(self):
        tid = uuid.uuid4()
        uid = uuid.uuid4()
        user = User(
            id=uid,
            tenant_id=tid,
            email="student@vtu.ac.in",
            password_hash="argon2id$hashed",
            full_name="Akash Patil",
            role="student",
        )
        self.assertEqual(user.email, "student@vtu.ac.in")
        self.assertEqual(user.role, "student")

        profile = UserProfile(
            tenant_id=tid,
            user_id=uid,
            age=21,
            state="Karnataka",
            social_category="OBC",
            annual_family_income_minor=15000000,
        )
        self.assertEqual(profile.age, 21)
        self.assertEqual(profile.annual_family_income_minor, 15000000)

    def test_transaction_minor_units(self):
        tid = uuid.uuid4()
        uid = uuid.uuid4()
        cid = uuid.uuid4()
        txn = Transaction(
            tenant_id=tid,
            user_id=uid,
            client_id=cid,
            amount_minor=25000,
            currency="INR",
            kind="DEBIT",
            category="food",
            payment_mode="UPI",
            occurred_on=date.today(),
        )
        self.assertEqual(txn.amount_minor, 25000)
        self.assertEqual(txn.kind, "DEBIT")
        self.assertEqual(txn.payment_mode, "UPI")


if __name__ == "__main__":
    unittest.main()
