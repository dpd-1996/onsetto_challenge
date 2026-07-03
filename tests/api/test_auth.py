"""API: authentication flow and bearer-token enforcement."""
import pytest

from config.settings import settings
from utils import data_factory as df

pytestmark = pytest.mark.api


def test_full_auth_flow_returns_bearer_token(api_client):
    token = api_client.authenticate(
        settings.USERNAME, settings.PASSWORD, settings.MFA_SECRET
    )
    assert token, "Expected a non-empty access token"


def test_token_step_returns_mfa_challenge_schema(api_client):
    """POST /auth/token must return the documented MFA-challenge schema."""
    resp = api_client.request_token(settings.USERNAME, settings.PASSWORD)
    assert resp.status_code == 200

    body = resp.json()
    assert body.get("mfa_required") is True
    assert body.get("mfa_token"), "Expected a non-empty mfa_token"


def test_mfa_step_returns_bearer_token_schema(api_client):
    """POST /auth/mfa/verify must return the documented bearer-token schema."""
    token_resp = api_client.request_token(settings.USERNAME, settings.PASSWORD)
    mfa_token = token_resp.json()["mfa_token"]

    resp = api_client.verify_mfa(mfa_token, settings.MFA_SECRET)
    assert resp.status_code == 200

    body = resp.json()
    assert body.get("access_token"), "Expected a non-empty access_token"
    assert body.get("token_type") == "Bearer"
    assert isinstance(body.get("expires_in"), int)


@pytest.mark.negative
def test_bad_credentials_are_rejected(api_client):
    """Wrong password must not yield an MFA challenge or a token."""
    resp = api_client.request_token(settings.USERNAME, "definitely-wrong-password")
    assert resp.status_code in (400, 401, 403)
    assert "mfa_token" not in resp.text.lower()


@pytest.mark.negative
def test_wrong_mfa_code_is_rejected(api_client):
    """A valid mfa_token with the wrong code must not return a bearer token."""
    token_resp = api_client.request_token(settings.USERNAME, settings.PASSWORD)
    mfa_token = token_resp.json()["mfa_token"]

    resp = api_client.verify_mfa(mfa_token, "0000")  # wrong code (correct is 1234)
    assert resp.status_code in (400, 401, 403)
    assert "access_token" not in resp.text.lower()


@pytest.mark.negative
@pytest.mark.slow
def test_rate_limit_is_enforced(api_client):
    """Documented limit is 30 req/min; rapid calls must eventually return 429."""
    statuses = []
    for _ in range(35):
        statuses.append(
            api_client.request_token(settings.USERNAME, settings.PASSWORD).status_code
        )
        if 429 in statuses:
            break
    assert 429 in statuses, f"Expected a 429 rate-limit response, saw: {set(statuses)}"


def test_banking_update_without_token_is_rejected(api_client):
    details = df.valid_banking()
    resp = api_client.update_banking(
        details.routing_number, details.account_number, token=""
    )
    assert resp.status_code in (401, 403)
    # An unauthenticated response must not leak stored account data.
    body = resp.text.lower()
    assert details.account_number not in body
    assert details.routing_number not in body


def test_banking_update_with_invalid_token_is_rejected(api_client):
    details = df.valid_banking()
    resp = api_client.update_banking(
        details.routing_number, details.account_number, token="not-a-real-token"
    )
    assert resp.status_code in (401, 403)
    assert details.account_number not in resp.text


@pytest.mark.negative
def test_payment_update_without_token_is_rejected(api_client):
    """Mirror of the banking auth guard for the payment endpoint."""
    details = df.valid_payment()
    resp = api_client.update_payment(
        details.cardholder_name,
        details.card_number,
        details.expiry,
        details.cvc,
        token="",
    )
    assert resp.status_code in (401, 403)
    # Sensitive values must never leak on an unauthenticated response.
    assert details.card_number not in resp.text
    assert details.cvc not in resp.text