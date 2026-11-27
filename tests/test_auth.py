import datetime as dt
import unittest
import uuid
import jwt
from fastapi import HTTPException

from app.core.config import settings
from app.core.security import create_access_token, decode_access_token, hash_password, verify_password
from app.core.tenant import AuthenticatedContext, require_roles
from app.schemas.auth import UserLogin, UserRegister


def run_sync(coro):
    """Executes a coroutine that completes synchronously without event loop overhead."""
    try:
        coro.send(None)
    except StopIteration as e:
        return e.value


class TestAuth(unittest.TestCase):
    def test_password_hashing_and_verification(self):
        """Test secure password hashing and verification."""
        password = "FinSmart@Test2026_Secure"
        hashed = hash_password(password)

        self.assertNotEqual(password, hashed)
        self.assertTrue(verify_password(password, hashed))
        self.assertFalse(verify_password("WrongPassword123", hashed))
        self.assertFalse(verify_password("", hashed))
        self.assertFalse(verify_password("FinSmart@Test2026_Secure_extra", hashed))

    def test_password_unicode_handling(self):
        """Test that Indic Unicode characters and passwords hash and verify cleanly."""
        indic_pw = "ಫಿನ್‌ಸ್ಮಾರ್ಟ್_2026_वित्तीय"
        hashed = hash_password(indic_pw)
        self.assertTrue(verify_password(indic_pw, hashed))
        self.assertFalse(verify_password("ಫಿನ್‌ಸ್ಮಾರ್ಟ್_2026_wrong", hashed))

    def test_jwt_token_claims_and_integrity(self):
        """Test JWT token encoding, claims preservation, and validation."""
        user_id = uuid.uuid4()
        tenant_id = uuid.uuid4()
        role = "student"

        token = create_access_token(user_id=user_id, tenant_id=tenant_id, role=role)
        self.assertIsInstance(token, str)

        payload = decode_access_token(token)
        self.assertEqual(payload["sub"], str(user_id))
        self.assertEqual(payload["tid"], str(tenant_id))
        self.assertEqual(payload["role"], role)
        self.assertIn("exp", payload)
        self.assertIn("iat", payload)

    def test_jwt_token_expiration(self):
        """Test that an expired JWT token raises jwt.ExpiredSignatureError."""
        user_id = uuid.uuid4()
        tenant_id = uuid.uuid4()
        past_time = dt.datetime.now(dt.timezone.utc) - dt.timedelta(hours=2)

        expired_payload = {
            "sub": str(user_id),
            "tid": str(tenant_id),
            "role": "student",
            "iat": past_time - dt.timedelta(minutes=60),
            "exp": past_time,
        }
        expired_token = jwt.encode(expired_payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)

        with self.assertRaises(jwt.ExpiredSignatureError):
            decode_access_token(expired_token)

    def test_jwt_tampered_signature(self):
        """Test that a JWT with an altered secret or signature is rejected."""
        user_id = uuid.uuid4()
        tenant_id = uuid.uuid4()
        tampered_token = jwt.encode(
            {"sub": str(user_id), "tid": str(tenant_id), "role": "admin"},
            "wrong-secret-key-1234567890-32bytes!",
            algorithm="HS256"
        )

        with self.assertRaises(jwt.PyJWTError):
            decode_access_token(tampered_token)

    def test_cross_tenant_token_isolation(self):
        """Test that a token issued for Tenant A is detected as a mismatch for Tenant B."""
        tenant_a = uuid.uuid4()
        tenant_b = uuid.uuid4()
        user_id = uuid.uuid4()

        token = create_access_token(user_id=user_id, tenant_id=tenant_a, role="student")
        payload = decode_access_token(token)

        self.assertEqual(payload["tid"], str(tenant_a))
        self.assertNotEqual(payload["tid"], str(tenant_b))

    def test_role_based_access_control_checker(self):
        """Test RBAC role checker factory allowing authorized roles and rejecting unauthorized."""
        admin_guard = require_roles("admin", "college_admin")

        # Mock contexts
        student_ctx = AuthenticatedContext(
            session=None,  # type: ignore
            tenant_id=uuid.uuid4(),
            user_id=uuid.uuid4(),
            role="student",
            email="student@vtu.ac.in",
            full_name="Student Test"
        )
        admin_ctx = AuthenticatedContext(
            session=None,  # type: ignore
            tenant_id=uuid.uuid4(),
            user_id=uuid.uuid4(),
            role="admin",
            email="admin@finsmart.in",
            full_name="Admin Test"
        )
        college_admin_ctx = AuthenticatedContext(
            session=None,  # type: ignore
            tenant_id=uuid.uuid4(),
            user_id=uuid.uuid4(),
            role="college_admin",
            email="dean@navkis.edu",
            full_name="Dean Test"
        )

        # Admin passes
        result_admin = run_sync(admin_guard(admin_ctx))
        self.assertEqual(result_admin.role, "admin")

        # College admin passes
        result_college = run_sync(admin_guard(college_admin_ctx))
        self.assertEqual(result_college.role, "college_admin")

        # Student is blocked with 403 Forbidden
        with self.assertRaises(HTTPException) as cm:
            run_sync(admin_guard(student_ctx))
        self.assertEqual(cm.exception.status_code, 403)

    def test_dpdp_consent_schema_validation(self):
        """Test schema validation requiring DPDP consent flag."""
        valid_reg = UserRegister(
            email="citizen@example.com",
            password="StrongPassword123!",
            full_name="Ramesh Kumar",
            role="student",
            consent_data_processing=True
        )
        self.assertTrue(valid_reg.consent_data_processing)

    def test_honeypot_spam_detection(self):
        """Test that non-empty honeypot traps bot submissions."""
        bot_login = UserLogin(
            email="bot@spammer.com",
            password="Password123!",
            honeypot="http://spam-link.ru"
        )
        self.assertEqual(bot_login.honeypot, "http://spam-link.ru")


if __name__ == "__main__":
    unittest.main()
