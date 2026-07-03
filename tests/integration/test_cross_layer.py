"""Cross-layer data-integrity checks.

The failure that matters for Onsetto: the UI shows one thing while the system
actually stored another. We update via the API, then read the UI's
'last updated' summary and assert the masked confirmation agrees across layers.
"""
import pytest

from utils import data_factory as df

pytestmark = [pytest.mark.integration]


def test_payment_last4_matches_between_api_and_ui(auth_api_client, account_page, parse_payment_summary):
    details = df.get_valid_card_details()

    api_resp = auth_api_client.update_payment(
        details.holder_name, details.card_number, details.exp_month, details.exp_year, details.cvc
    )
    assert api_resp.status_code == 200
    api_last4 = str(api_resp.json().get("last4"))
    print(f"API last4={api_last4}")

    # Re-load the account page so the UI reflects the persisted value.
    account_page.page.reload()
    card_last4, expiry = parse_payment_summary(account_page.payment_summary())
    print(f"UI last4={card_last4}")
    
    assert api_last4 == card_last4 == details.card_number[-4:], (
        f"Masked card mismatch across layers: API={api_last4!r} UI={card_last4!r}. "
        "If the two layers legitimately mask differently, document the difference "
        "instead of forcing a match."
    )


def test_banking_last4_matches_between_api_and_ui(auth_api_client, account_page, parse_banking_summary, last4):
    details = df.get_valid_account_details()

    api_resp = auth_api_client.update_banking(
        details.routing_number, details.account_number
    )
    assert api_resp.status_code == 200
    api_masked = str(api_resp.json().get("account_masked", ""))
    api_last4 = last4(api_masked)
    routing_masked = str(api_resp.json().get("routing_masked", ""))
    routing_last4 = last4(routing_masked)
    #print(f"API last4={api_last4}; routing last4={routing_last4}")

    account_page.page.reload()
    routing, account = parse_banking_summary(account_page.banking_summary())
    #print(f"UI last4={account}; routing last4={routing}")

    assert api_last4 == account == details.account_number[-4:], (
        f"Masked account mismatch across layers: API={api_last4!r} UI={account!r}. "
        "If the two layers legitimately mask differently, document the difference "
        "instead of forcing a match."
    )

    assert routing_last4 == routing == details.routing_number[-4:], (
        f"Masked routing mismatch across layers: API={routing_last4!r} UI={routing!r}. "
        "If the two layers legitimately mask differently, document the difference "
        "instead of forcing a match."
    )