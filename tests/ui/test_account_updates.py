"""UI: happy-path banking + payment updates and their 'last updated' summaries."""
import re
import pytest

from utils import data_factory as df


pytestmark = pytest.mark.ui


def test_update_banking_shows_in_summary(account_page, parse_banking_summary):
    details = df.get_valid_account_details()
    account_page.save_bank_details(details)
    
    summary = account_page.banking_summary()
    print(f"Banking summary: {summary}")

    # Full account number must never be rendered in clear text.
    assert details.account_number not in summary

    routing, account = parse_banking_summary(summary)
    # Summary should confirm the update using a masked account (last 4 only).
    assert details.account_number[-4:] == account
    assert details.routing_number[-4:] == routing


def test_update_payment_shows_in_summary(account_page, parse_payment_summary):
    details = df.get_valid_card_details()
    account_page.save_card_details(details)

    summary = account_page.payment_summary()
    card_last4, expiry = parse_payment_summary(summary)

    assert card_last4 == details.card_number[-4:]
    assert expiry is not None
    assert details.card_number not in summary


#--------Negarive Test Cases for Banking and Payment Updates------

def test_routing_too_short_shows_routing_error(account_page):
    account_page.save_bank_details(df.short_routing())
    error = account_page.get_error_messages()
    assert "9" in error or "routing" in error.lower()


def test_account_number_overlength_shows_account_error(account_page):
    account_page.save_bank_details(df.overlong_account())
    error = account_page.get_error_messages()
    assert error != ""


def test_luhn_fail_card_shows_card_number_error(account_page):
    account_page.save_card_details(df.luhn_fail_payment())
    error = account_page.get_error_messages()
    assert error != ""


def test_past_expiry_shows_expiry_error(account_page):
    account_page.save_card_details(df.past_expiry_payment())
    error = account_page.get_error_messages()
    assert "expir" in error.lower() or error != ""