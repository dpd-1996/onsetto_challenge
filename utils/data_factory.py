from dataclasses import dataclass
from datetime import date
from utils.luhn import make_luhn_invalid

@dataclass
class AccountDetails:
    routing_number: str
    account_number: str


@dataclass
class CardDetails:
    holder_name: str
    card_number: str
    exp_month: str
    exp_year: str
    cvc: str


def _future_expiry(years_ahead: int = 3) -> str:
    today = date.today()
    exp_month = f"{today.month:02d}"  # Format month as two digits
    exp_year = f"{today.year + years_ahead:04d}"  # Format year as four digits
    return exp_month, exp_year

def _past_expiry(years_behind: int = 3) -> str:
    today = date.today()
    exp_month = f"{today.month:02d}" 
    exp_year = f"{today.year - years_behind:04d}"
    return exp_month, exp_year

def get_valid_account_details() -> AccountDetails:
    return AccountDetails(routing_number="123456789", account_number="987654321")

def get_valid_card_details() -> CardDetails:
    exp_month, exp_year = _future_expiry()
    return CardDetails(
        holder_name="John Doe",
        card_number="4111111111111111",
        exp_month=exp_month,
        exp_year=exp_year,
        cvc="123"
    )

# ---Negative

def short_routing() -> AccountDetails:
    d = get_valid_account_details()
    d.routing_number = "02100002"  # 8 digits -> invalid
    return d


def overlong_account() -> AccountDetails:
    d = get_valid_account_details()
    d.account_number = "1" * 18  # > 17 digits -> invalid
    return d


def luhn_fail_payment() -> CardDetails:
    d = get_valid_card_details()
    d.card_number = make_luhn_invalid(d.card_number)
    return d


def past_expiry_payment() -> CardDetails:
    d = get_valid_card_details()
    exp_month, exp_year = _past_expiry()
    d.exp_month = exp_month
    d.exp_year = exp_year
    return d