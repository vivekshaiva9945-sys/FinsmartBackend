import unittest
import uuid
from app.core.security import create_access_token, decode_access_token, hash_password, verify_password


class TestSecurity(unittest.TestCase):
    def test_password_hash_and_verify(self):
        pw = "FinSmartSecure2026!"
        hashed = hash_password(pw)
        self.assertNotEqual(pw, hashed)
        self.assertTrue(verify_password(pw, hashed))
        self.assertFalse(verify_password("WrongPassword123", hashed))

    def test_jwt_access_token_creation_and_claims(self):
        user_id = uuid.uuid4()
        tenant_id = uuid.uuid4()
        role = "student"
        
        token = create_access_token(user_id=user_id, tenant_id=tenant_id, role=role)
        self.assertIsInstance(token, str)
        
        decoded = decode_access_token(token)
        self.assertEqual(decoded["sub"], str(user_id))
        self.assertEqual(decoded["tid"], str(tenant_id))
        self.assertEqual(decoded["role"], role)
        self.assertIn("exp", decoded)


if __name__ == "__main__":
    unittest.main()

