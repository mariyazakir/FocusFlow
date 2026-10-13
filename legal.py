"""Small, testable policy-consent rules shared by the Streamlit interface."""

LEGAL_VERSION = "2026-10-12-v3"


def can_accept_policies(terms_agreed: bool, privacy_acknowledged: bool) -> bool:
    """Require acknowledgement of both policy documents to continue."""
    return bool(terms_agreed and privacy_acknowledged)
