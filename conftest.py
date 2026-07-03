"""Shared pytest fixtures for both UI (Playwright) and API (requests) layers."""
import re
import json
import pytest

from api_client.client import APIClient
from config.settings import settings
from pages.account_page import AccountPage
from pages.login_page import LoginPage


# --------------------------------------------------------------------------- #
# API fixtures
# --------------------------------------------------------------------------- #
@pytest.fixture
def api_client() -> APIClient:
    return APIClient(settings.API_BASE_URL)


@pytest.fixture
def auth_api_client(api_client: APIClient) -> APIClient:
    """API client with a valid bearer token already obtained."""
    api_client.authenticate(settings.USERNAME, settings.PASSWORD, settings.MFA_SECRET)
    return api_client


# --------------------------------------------------------------------------- #
# UI fixtures — authenticate ONCE, reuse storage state across UI tests
# --------------------------------------------------------------------------- #
@pytest.fixture(scope="session")
def browser_type_launch_args():
    """Return a dict of launch-time options for the browser."""
    return {"headless": settings.HEADLESS.lower() == "true", "slow_mo": 50}

@pytest.fixture(scope="session")
def storage_state_path(browser, tmp_path_factory) -> str:
    """Log in + complete MFA once, then persist the session storage state."""
    state_file = tmp_path_factory.getbasetemp() / "storage_state.json"

    # `headless` is a launch-time option, not a context option. Use base_url here.
    context = browser.new_context(base_url=settings.BASE_URL)
    page = context.new_page()
    lp = LoginPage(page)
    lp.goto(settings.BASE_URL)
    lp.navigate()
    lp.login(settings.USERNAME, settings.PASSWORD)
    lp.submit_code(settings.MFA_SECRET)
    context.storage_state(path=str(state_file))
    session_storage = page.evaluate("() => JSON.stringify(window.sessionStorage)")
    context.close()
    return {"state_file": str(state_file), "session_storage": session_storage}


@pytest.fixture
def authed_page(browser, storage_state_path):
    # Do not pass `headless` to new_context(); the browser is launched by the
    # test runner. Provide base_url and the saved storage state instead.
    context = browser.new_context(
        base_url=settings.BASE_URL, storage_state=storage_state_path["state_file"]
    )
    context.add_init_script(
        """(storage => {
            const entries = JSON.parse(storage);
            for (const [key, value] of Object.entries(entries)) {
                window.sessionStorage.setItem(key, value);
            }
        })(%s)"""
    )
    page = context.new_page()
    page.goto("/app/marketplace")
    LoginPage(page).submit_code(settings.MFA_SECRET)  # Ensure we're fully authenticated    
    yield page
    context.close()


@pytest.fixture
def account_page(authed_page) -> AccountPage:
    account = AccountPage(authed_page)
    account.navigate_to_account_page()
    
    return account


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #
@pytest.fixture
def last4():
    """Extract the last 4 visible digits from a masked string like '•••• 4242'."""

    def _last4(masked: str) -> str:
        digits = re.findall(r"\d", masked)
        return "".join(digits[-4:])

    return _last4

@pytest.fixture
def parse_banking_summary():
    def _parse(summary: str) -> tuple[str | None, str | None]:
        """Extract masked routing and account values from the banking summary."""
        normalized = summary.replace("\xa0", " ").strip()
        routing_match = re.search(r"Routing:\s*[^\d]*(\d+)", normalized)
        account_match = re.search(r"Account:\s*[^\d]*(\d+)", normalized)
        routing = routing_match.group(1) if routing_match else None
        account = account_match.group(1) if account_match else None
        return routing, account
    return _parse


@pytest.fixture
def parse_payment_summary():
    def _parse(summary: str) -> tuple[str | None, str | None]:
        """Extract card last 4 digits and expiry date from the payment summary."""
        normalized = summary.replace("\xa0", " ").strip()
        card_match = re.search(r"VISA ending in\s*(\d{4})", normalized, re.IGNORECASE)
        expiry_match = re.search(r"Expires\s*(\d{1,2}/\d{4})", normalized, re.IGNORECASE)
        card_last4 = card_match.group(1) if card_match else None
        expiry = expiry_match.group(1) if expiry_match else None
        return card_last4, expiry
    return _parse

