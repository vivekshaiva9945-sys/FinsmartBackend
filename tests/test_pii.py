import unittest
from app.core.pii import contains_pii, scrub_pii


class TestPIIRedaction(unittest.TestCase):
    def test_aadhaar_scrubbing(self):
        text_with_aadhaar = "My Aadhaar number is 5482 1234 5678 and need scholarship."
        scrubbed = scrub_pii(text_with_aadhaar)
        self.assertNotIn("5482 1234 5678", scrubbed)
        self.assertIn("[AADHAAR_REDACTED]", scrubbed)

    def test_pan_scrubbing(self):
        text_with_pan = "Income verification PAN is ABCDE1234F."
        scrubbed = scrub_pii(text_with_pan)
        self.assertNotIn("ABCDE1234F", scrubbed)
        self.assertIn("[PAN_REDACTED]", scrubbed)

    def test_phone_scrubbing(self):
        text_with_phone = "Contact me at +91 9876543210 regarding loan."
        scrubbed = scrub_pii(text_with_phone)
        self.assertNotIn("9876543210", scrubbed)
        self.assertIn("[PHONE_REDACTED]", scrubbed)

    def test_contains_pii_flag(self):
        self.assertTrue(contains_pii("My phone is 9876543210"))
        self.assertFalse(contains_pii("How do I save money on groceries?"))


if __name__ == "__main__":
    unittest.main()

