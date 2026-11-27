import unittest
import uuid
import jwt
from fastapi import HTTPException
from pydantic import ValidationError

from app.core.config import Settings
from app.core.pii import contains_pii, scrub_pii
from app.core.security import create_access_token, decode_access_token
from app.core.tenant import AuthenticatedContext, require_roles
from app.main import RATE_LIMITS
from app.schemas.consent import DSARDataExport
from app.services.ai_service import check_guardrails


def run_sync(coro):
    """Executes a coroutine that completes synchronously without event loop overhead."""
    try:
        coro.send(None)
    except StopIteration as e:
        return e.value


class TestSecurityAudit(unittest.TestCase):
    # -------------------------------------------------------------------------
    # 1. Cryptography, JWT and Secrets Security
    # -------------------------------------------------------------------------
    def test_production_jwt_secret_validation(self):
        """Verify that in production, default or weak JWT secrets are rejected immediately."""
        # In production with default secret, should raise ValidationError
        with self.assertRaises(ValidationError):
            Settings(
                environment="production",
                jwt_secret="super_secret_finsmart_jwt_key_at_least_32_characters_long_2026"
            )

        # In production with short secret, should raise ValidationError
        with self.assertRaises(ValidationError):
            Settings(
                environment="production",
                jwt_secret="short_secret"
            )

        # In production with strong 32+ char secret, should succeed
        strong_settings = Settings(
            environment="production",
            jwt_secret="a_very_strong_custom_production_secret_key_1234567890!"
        )
        self.assertEqual(strong_settings.environment, "production")

    def test_jwt_tampered_signature_rejection(self):
        """Verify that any token with a forged or tampered signature is rejected."""
        uid = uuid.uuid4()
        tid = uuid.uuid4()
        valid_token = create_access_token(user_id=uid, tenant_id=tid, role="student")
        
        # Tamper token signature
        tampered_token = valid_token[:-4] + "abcd"
        with self.assertRaises(jwt.PyJWTError):
            decode_access_token(tampered_token)

    def test_jwt_none_algorithm_rejection(self):
        """Verify that tokens using 'none' algorithm are strictly rejected."""
        # Attempt to forge an unsigned token with alg='none'
        forged_payload = {"sub": str(uuid.uuid4()), "tid": str(uuid.uuid4()), "role": "admin"}
        unsigned_token = jwt.encode(forged_payload, key="", algorithm="none")
        
        with self.assertRaises(jwt.PyJWTError):
            decode_access_token(unsigned_token)

    # -------------------------------------------------------------------------
    # 2. Multi-Tenancy & Authorization Boundaries
    # -------------------------------------------------------------------------
    def test_role_based_access_control_matrix(self):
        """Verify RBAC dependency strictly blocks unauthorized student roles from admin operations."""
        admin_guard = require_roles("college_admin", "admin")

        # Student user attempting admin action
        student_ctx = AuthenticatedContext(
            session=None,
            tenant_id=uuid.uuid4(),
            user_id=uuid.uuid4(),
            role="student",
            email="student@rvce.edu.in",
            full_name="Student"
        )
        with self.assertRaises(HTTPException) as cm:
            run_sync(admin_guard(student_ctx))
        self.assertEqual(cm.exception.status_code, 403)

        # Admin user allowed
        admin_ctx = AuthenticatedContext(
            session=None,
            tenant_id=uuid.uuid4(),
            user_id=uuid.uuid4(),
            role="college_admin",
            email="admin@rvce.edu.in",
            full_name="Admin"
        )
        allowed = run_sync(admin_guard(admin_ctx))
        self.assertEqual(allowed.role, "college_admin")

    # -------------------------------------------------------------------------
    # 3. DPDP Act 2023 & Sensitive Data Exposure
    # -------------------------------------------------------------------------
    def test_pii_scrubber_indian_identifiers(self):
        """Verify PII scrubber strips Aadhaar, PAN, phone numbers, and payment cards."""
        text_with_pii = (
            "My Aadhaar is 5421 8901 2345, my PAN is ABCDE1234F, "
            "contact me at +91 9876543210 and card 4111 2222 3333 4444."
        )
        self.assertTrue(contains_pii(text_with_pii))

        scrubbed = scrub_pii(text_with_pii)
        self.assertNotIn("5421 8901 2345", scrubbed)
        self.assertNotIn("ABCDE1234F", scrubbed)
        self.assertNotIn("9876543210", scrubbed)
        self.assertNotIn("4111 2222 3333 4444", scrubbed)
        self.assertIn("[AADHAAR_REDACTED]", scrubbed)
        self.assertIn("[PAN_REDACTED]", scrubbed)
        self.assertIn("[PHONE_REDACTED]", scrubbed)
        self.assertIn("[CARD_NUMBER_REDACTED]", scrubbed)

    def test_dsar_export_schema_excludes_password_hash(self):
        """Verify DSAR data portability schema strictly omits user password hash."""
        fields = DSARDataExport.model_fields.keys()
        self.assertIn("user", fields)
        self.assertIn("transactions", fields)
        self.assertIn("budgets", fields)
        self.assertIn("goals", fields)
        self.assertIn("consents", fields)
        # Ensure password_hash is not a top-level field or in export documentation
        self.assertNotIn("password_hash", fields)
        self.assertNotIn("password", fields)

    # -------------------------------------------------------------------------
    # 4. AI Guardrails & Financial Refusal
    # -------------------------------------------------------------------------
    def test_ai_speculative_refusal_guardrails(self):
        """Verify AI assistant strictly refuses crypto speculation and get-rich tips."""
        risky_queries = [
            "Which crypto should I buy today for fast returns?",
            "Give me intraday options tips for guaranteed profit",
            "How to double my money in 10 days using bitcoin?",
            "What are the best stocks to buy right now?",
            "Tell me about online rummy and casino betting tips"
        ]
        for q in risky_queries:
            refusal = check_guardrails(q)
            self.assertIsNotNone(refusal, f"Failed to refuse risky query: {q}")
            self.assertIn("FinSmart is an educational financial literacy platform", refusal)
            self.assertIn("SEBI and RBI guidelines caution against speculative schemes", refusal)

    # -------------------------------------------------------------------------
    # 5. Rate Limiting Coverage
    # -------------------------------------------------------------------------
    def test_rate_limiting_sensitive_routes_configured(self):
        """Verify rate limits are strictly established for sensitive endpoints."""
        self.assertIn("/v1/auth/login", RATE_LIMITS)
        self.assertIn("/v1/auth/register", RATE_LIMITS)
        self.assertIn("/v1/ai/chat", RATE_LIMITS)
        self.assertIn("/v1/profiles/erasure", RATE_LIMITS)
        self.assertIn("/v1/profiles/dsar-export", RATE_LIMITS)

        # Ensure high-cost AI route is capped at <= 20 requests/minute
        self.assertLessEqual(RATE_LIMITS["/v1/ai/chat"], 20)
        # Ensure auth routes are protected against brute force
        self.assertLessEqual(RATE_LIMITS["/v1/auth/login"], 15)
        self.assertLessEqual(RATE_LIMITS["/v1/auth/register"], 10)


if __name__ == "__main__":
    unittest.main()
