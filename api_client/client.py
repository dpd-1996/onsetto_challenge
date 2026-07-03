from typing import Optional

import requests


class APIClient:
    def __init__(self, base_url: str, session: Optional[requests.Session] = None) -> None:
        self.base_url = base_url.rstrip("/")
        self.session = session or requests.Session()
        self.token: Optional[str] = None

    def _url(self, path: str) -> str:
        return f"{self.base_url}{path}"

    def _auth_headers(self) -> dict:
        if not self.token:
            return {}
        return {"Authorization": f"Bearer {self.token}"}

    def request_token(self, username: str, password: str) -> requests.Response:
        # Per API Docs the credential field is `email` (the username IS the email).
        return self.session.post(
            self._url("/auth/token"),
            json={"email": username, "password": password},
        )

    def verify_mfa(self, mfa_token: str, code: str) -> requests.Response:
        return self.session.post(
            self._url("/auth/mfa/verify"),
            json={"mfa_token": mfa_token, "code": code},
        )

    def authenticate(self, username: str, password: str, code: str) -> Optional[str]:
        """Run the full token + MFA flow and store the bearer token."""
        token_resp = self.request_token(username, password)
        token_resp.raise_for_status()
        mfa_token = token_resp.json().get("mfa_token", "")

        mfa_resp = self.verify_mfa(mfa_token, code)
        mfa_resp.raise_for_status()
        self.token = mfa_resp.json().get("access_token")
        return self.token

    def update_banking(
        self, routing_number: str, account_number: str, token: Optional[str] = None
    ) -> requests.Response:
        headers = (
            {"Authorization": f"Bearer {token}"}
            if token is not None
            else self._auth_headers()
        )
        return self.session.put(
            self._url("/account/banking"),
            json={"routing_number": routing_number, "account_number": account_number},
            headers=headers,
        )

    def update_payment(
        self,
        cardholder_name: str,
        card_number: str,
        exp_month: int,
        exp_year: int,
        cvc: str,
        token: Optional[str] = None,
    ) -> requests.Response:
        headers = (
            {"Authorization": f"Bearer {token}"}
            if token is not None
            else self._auth_headers()
        )

        return self.session.put(
            self._url("/account/payment"),
            json={
                "cardholder_name": cardholder_name,
                "card_number": card_number,
                "exp_month": exp_month,
                "exp_year": exp_year,
                "cvc": cvc,
            },
            headers=headers,
        )


def _split_expiry(expiry: str) -> tuple[int, int]:
    """Split an "MM/YY" or "MM/YYYY" expiry string into (month, 4-digit year)."""
    month_str, year_str = expiry.split("/")
    month = int(month_str)
    year = int(year_str)
    if year < 100:  # normalise 2-digit years (e.g. "30" -> 2030)
        year += 2000
    return month, year