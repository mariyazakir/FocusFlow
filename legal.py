"""Small, testable policy-consent rules shared by the Streamlit interface."""

LEGAL_VERSION = "2026-10-12-v2"


def can_accept_for_adult_release(
    terms_agreed: bool, privacy_acknowledged: bool, adult_confirmed: bool
) -> bool:
    """Require every acknowledgement for the current adult-only release."""
    return bool(terms_agreed and privacy_acknowledged and adult_confirmed)
