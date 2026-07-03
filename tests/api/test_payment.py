"""API: PUT /account/payment — contract + validation."""
import pytest

from utils import data_factory as df

pytestmark = pytest.mark.api


def test_valid_payment_update_returns_masked_last4(auth_api_client):
    details = df.get_valid_card_details()
    resp = auth_api_client.update_payment(
        details.holder_name, details.card_number, details.exp_month, details.exp_year, details.cvc
    )
    assert resp.status_code == 200

    body = resp.json()
    # Documented response schema: card_brand, last4, exp_month, exp_year, token.
    for field in ("card_brand", "last4", "exp_month", "exp_year", "token"):
        assert field in body, f"missing '{field}' in payment response: {body}"

    assert str(body["last4"]) == details.card_number[-4:]
    # Sensitive values must never be returned in clear text.
    assert details.card_number not in resp.text
    assert details.cvc not in resp.text


def test_luhn_fail_card_is_rejected(auth_api_client):
    details = df.luhn_fail_payment()
    resp = auth_api_client.update_payment(
        details.holder_name, details.card_number, details.exp_month, details.exp_year, details.cvc
    )
    assert resp.status_code in (400, 422)
    assert "card" in str(resp.json()).lower()


def test_past_expiry_is_rejected(auth_api_client):
    details = df.past_expiry_payment()
    resp = auth_api_client.update_payment(
        details.holder_name, details.card_number, details.exp_month, details.exp_year, details.cvc
    )
    assert resp.status_code in (400, 422)