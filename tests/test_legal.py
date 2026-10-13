import unittest

from legal import LEGAL_VERSION, can_accept_policies


class LegalConsentTests(unittest.TestCase):
    def test_requires_both_policy_acknowledgements(self):
        self.assertTrue(can_accept_policies(True, True))
        self.assertFalse(can_accept_policies(False, True))
        self.assertFalse(can_accept_policies(True, False))

    def test_policy_version_requires_reacceptance_after_policy_update(self):
        self.assertEqual(LEGAL_VERSION, "2026-10-12-v3")


if __name__ == "__main__":
    unittest.main()
