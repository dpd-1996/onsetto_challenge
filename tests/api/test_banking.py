"""API: PUT /account/banking — contract + validation."""
import pytest

from utils import data_factory as df

pytestmark = pytest.mark.api


def test_valid_banking_update_returns_masked_confirmation(auth_api_client):
    details = df.get_valid_account_details()
    resp = auth_api_client.update_banking(
        details.routing_number, details.account_number
    )
    assert resp.status_code == 200

    body = resp.json()
    # Documented response schema: routing_masked, account_masked, token.
    for field in ("routing_masked", "account_masked", "token"):
        assert field in body, f"missing '{field}' in banking response: {body}"

    # Confirmation must be masked and must NOT echo the full account number.
    masked = str(body["account_masked"])
    assert details.account_number[-4:] in masked
    assert details.account_number not in resp.text
    assert details.routing_number not in resp.text
    # Masked fields must actually be masked (contain a masking marker).
    assert any(c in masked for c in "•*xX")


def test_invalid_routing_length_is_field_level_error(auth_api_client):
    details = df.short_routing()  # 8 digits
    resp = auth_api_client.update_banking(
        details.routing_number, details.account_number
    )
    assert resp.status_code in (400, 422)

    body = resp.json()
    text = str(body).lower()
    assert "routing" in text  # error is attributed to the routing field


def test_overlong_account_number_is_rejected(auth_api_client):
    details = df.overlong_account()  # 18 digits
    resp = auth_api_client.update_banking(
        details.routing_number, details.account_number
    )
    #print(f"Response: {resp.json()}")
    assert resp.json().get("error") is not None
    assert resp.status_code in (400, 422)