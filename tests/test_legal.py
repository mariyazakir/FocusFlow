import unittest

from legal import LEGAL_VERSION, can_accept_for_adult_release


class LegalConsentTests(unittest.TestCase):
    def test_requires_all_three_confirmations(self):
        self.assertTrue(can_accept_for_adult_release(True, True, True))
        self.assertFalse(can_accept_for_adult_release(False, True, True))
        self.assertFalse(can_accept_for_adult_release(True, False, True))
        self.assertFalse(can_accept_for_adult_release(True, True, False))

    def test_policy_version_requires_reacceptance_after_age_gate_change(self):
        self.assertEqual(LEGAL_VERSION, "2026-10-12-v2")


if __name__ == "__main__":
    unittest.main()
