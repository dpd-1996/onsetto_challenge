# Onsetto QA Automation Challenge

A single Python project covering both parts of the challenge:

- **Part 1 — UI automation** with **Playwright** using a **Page Object Model** and
  a fixture that performs the login + simulated-MFA flow for each UI test.
- **Part 2 — API tests + cross-layer data integrity** with **requests** + **pytest**.

---

## Project structure

```
.
├── conftest.py                 # shared fixtures (API clients + Playwright auth + last4 helper)
├── pytest.ini                  # markers + test discovery
├── requirements.txt            # pinned dependencies
├── .env                        # Actual values of env variables for env-driven config
│
├── config/
│   └── settings.py             # env-driven config (URLs, creds, MFA code, HEADLESS)
│
├── api_client/
│   └── client.py               # requests-based REST client (auth flow + account updates)
│
├── pages/                      # Page Object Model
│   ├── base_page.py            # shared page helpers (goto, text_of)
│   ├── login_page.py           # login + MFA form interactions
│   └── account_page.py         # /app/account banking + payment forms and summaries
│
├── utils/
│   ├── luhn.py                 # Luhn (mod-10) checksum helpers for card numbers
│   └── data_factory.py         # dataclasses + valid / negative / boundary test-data builders
│
└── tests/
    ├── api/
    │   ├── test_auth.py        # auth flow, token schema, bearer-token enforcement, rate limit
    │   ├── test_banking.py     # PUT /account/banking contract + validation
    │   └── test_payment.py     # PUT /account/payment contract + validation
    ├── integration/
    │   └── test_cross_layer.py # API ↔ UI masked-value integrity checks
    └── ui/
        └── test_account_updates.py # happy-path banking + payment summaries and inline errors
 
```

---

## Setup

```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS/Linux
source .venv/bin/activate

pip install -r requirements.txt
playwright install chromium

Create or update a .env file in the project root with the values below.
```

**Dependencies** (`requirements.txt`): `pytest==8.3.3`, `pytest-playwright==0.5.2`,
`playwright==1.47.0`, `requests==2.32.3`, `python-dotenv==1.0.1`,
`pytest-html==4.1.0`.

### Environment variables (`.env`)

Loaded via `python-dotenv` in `config/settings.py`. All values must be supplied
via `.env` (no defaults are baked in).

| Var | Purpose |
| --- | --- |
| `BASE_URL` | Web app base URL |
| `API_BASE_URL` | API base URL |
| `USERNAME` | Test user email (used as the `email` credential) |
| `PASSWORD` | Test user password |
| `MFA_SECRET` | Simulated MFA code (the live app uses `1234`) |
| `HEADLESS` | `true`/`false` for Playwright; set it explicitly for UI runs |


---

## Running

```bash
pytest                            # everything
pytest -m api                     # API tests only
pytest -m ui                      # UI tests only
pytest -m integration             # cross-layer data-integrity tests
pytest -m negative                # negative / boundary cases
pytest -m "not slow"             # skip the rate-limit test that fires many requests
```

Run headed while debugging UI:

```bash
HEADLESS=false pytest -m ui --headed
```

Generate an HTML test report:

```bash
pytest --html=reports/report.html --self-contained-html
```

Generate the report for a specific suite:

```bash
pytest -m api --html=reports/api-report.html --self-contained-html
```

### Markers (`pytest.ini`)

| Marker | Meaning |
| --- | --- |
| `ui` | Playwright UI tests |
| `api` | REST API tests |
| `integration` | cross-layer UI + API data-integrity tests |
| `negative` | negative / boundary validation tests |
| `slow` | tests that intentionally make many requests (e.g. rate-limit checks) |

`addopts = -ra -q --strict-markers` and `testpaths = tests` are set, so unknown
markers fail fast and discovery is scoped to `tests/`.

---

## Fixtures (`conftest.py`)

- `api_client` — a fresh `APIClient` pointed at `API_BASE_URL` (no token).
- `auth_api_client` — an `APIClient` that has already run the full
  `POST /auth/token` → `POST /auth/mfa/verify` flow and holds a bearer token.
- `browser_type_launch_args` — session-scoped; lets `settings.HEADLESS` drive
  Playwright's headless mode.
- `authed_page` — a fresh browser context that performs **login + MFA on the same
  page** the test will use. MFA is mandatory on every session, so storage-state
  reuse is not viable; the per-tab `sessionStorage` token stays valid only within
  the page that authenticated. The context is closed on teardown.
- `account_page` — an `AccountPage` built on `authed_page` and already navigated
  to `/app/account`.
- `storage_state_path` — creates the browser context, completes the login/MFA
  flow once, and persists the session state for the Playwright session.
- `last4` — helper that extracts the trailing 4 digits from a masked string like
  `•••• 4242`, used by the cross-layer and UI payment assertions.
- `parse_banking_summary` / `parse_payment_summary` — small helpers that parse the
  UI summary text into masked routing/account values and payment expiry details.


---

## Test scenarios covered

**API — auth & token enforcement (`tests/api/test_auth.py`)**
- Full `POST /auth/token` → `POST /auth/mfa/verify` flow returns a bearer token.
- `POST /auth/token` returns the documented MFA-challenge schema
  (`mfa_required`, `mfa_token`).
- `POST /auth/mfa/verify` returns the documented bearer schema
  (`access_token`, `token_type == "Bearer"`, integer `expires_in`).
- Negative: bad password yields no MFA challenge/token; wrong MFA code yields no
  bearer token.
- `slow`: rapid `/auth/token` calls eventually return `429` (documented 30/min).
- Banking update with an **empty** or **invalid** bearer token is rejected
  (`401/403`) and leaks no routing/account data.
- Payment update with a missing token is rejected and leaks no card number/CVC.

**API — banking (`tests/api/test_banking.py`)**
- Valid update returns the documented masked confirmation
  (`routing_masked`, `account_masked`, `token`); the masked account contains the
  last 4 digits, carries a masking marker (`•*xX`), and never echoes the full
  account or routing number.
- Invalid routing length (8 digits) is a field-level error (`400/422`,
  message attributed to the routing field).
- Over-length account number (18 digits) is rejected (`400/422`).

**API — payment (`tests/api/test_payment.py`)**
- Valid update returns the documented schema
  (`card_brand`, `last4`, `exp_month`, `exp_year`, `token`); `last4` matches the
  card's last 4 and neither the full PAN nor the CVC is returned in clear text.
- Luhn-fail card is rejected (`400/422`, error attributed to the card).
- Past expiry is rejected (`400/422`).

**UI — account update flows (`tests/ui/test_account_updates.py`)**
- Submit valid banking details; the "last updated" summary shows the account
  last-4 and never the full number.
- Submit a valid payment method; the summary's card last-4 matches, and the full
  number is never shown.
- Negative cases in the same suite exercise invalid routing/account/card and
  past-expiry flows and assert the visible error messages surfaced by the page
  object.

**Cross-layer — the part that matters (`tests/integration/test_cross_layer.py`)**
- Update payment via API, reload the UI, and assert the API `last4`, the UI
  summary last-4, and the card's actual last-4 all agree.
- Same masked-value agreement for banking (`account_masked` last-4 vs UI summary).

**Utility checks (`utils/luhn.py`)**
- A known Luhn-valid number passes the checksum helper.
- The helper can also produce a near-identical number that fails the checksum.

---

## API client & data factory notes

- `api_client/client.py` implements the two-step auth (`request_token` → `verify_mfa`,
  wrapped by `authenticate`) plus `update_banking` / `update_payment`. Both
  update methods accept an optional `token` override so the auth-guard tests can
  send an empty or bogus bearer token. `update_payment` splits the fixture's
  `MM/YYYY` expiry into the integer `exp_month` / `exp_year` the API documents.
- `utils/data_factory.py` provides `AccountDetails` / `CardDetails`
  dataclasses and builders such as `get_valid_account_details`,
  `get_valid_card_details`, `short_routing`, `overlong_account`,
  `luhn_fail_payment`, and `past_expiry_payment`. Expiry values are generated
  relative to today so tests stay valid over time.

---

## What class of bug the cross-layer check catches

It catches **write/display divergence** — where the persisted value and the value
shown to the user disagree. For a company that switches real bank accounts, the
dangerous failure is when the UI confirms "•••• 4242" but the backend actually
stored a different account/card (truncation, off-by-one masking, a stale cached
summary, wrong record updated, or last-4 derived from a different field).

- A **UI-only** test would happily pass because the summary *looks* correct — it
  never checks what was truly stored server-side.
- A **status-code-only** API test passes on `200 OK` — it never checks that the
  masked confirmation corresponds to what the user sees.

Only by asserting the API's masked confirmation **equals** the UI's displayed
mask do we prove both layers describe the *same* stored value. If the two layers
legitimately mask differently (e.g. `•••• 4242` vs `XXXXXXXXXXXX4242`), the test
message says to document the difference rather than force a match; the helper
compares on the trailing 4 digits to stay robust to formatting.

---

## Approach & tradeoffs (timeboxed ~3–4h)

- **One project, shared fixtures** so the cross-layer test can drive both layers.
- **POM + login-per-UI-test fixture**: because the app enforces MFA on every
  session, the `authed_page` fixture logs in and completes MFA on the same page
  the test uses (the token lives in per-tab `sessionStorage`), rather than
  capturing and replaying `storage_state`.
- **Selectors** follow the challenge's stable `id` / `data-testid` convention
  (`#bank-routing`, `#card-number`, `#card-save`, `[data-testid='card-number-error']`, …).
  Login/MFA selectors and API JSON field names are best-effort against the
  documented contract and are the first thing to align against the live app.
- Status-code assertions accept a small set (`401/403`, `400/422`) to stay
  resilient to reasonable API choices without being lax on the security intent.

### Not done / would extend
- Add the `testdata/ui/*.json` fixtures and the `utils/testdata` loader
  (`load_json`/`ids`) that the parametrized UI validation test expects, and
  reconcile the `conftest` page-object import path with the `pages/` package.
- Wire real values from the API Docs page and reconcile any selector/field-name
  differences with the live app.
- CI workflow (GitHub Actions) + Allure reporting and trace-on-failure.- Screenshot-on-failure support for UI test debugging and evidence capture.- Data-driven parametrization for more boundary values (min/max lengths, 3 vs 4
  digit CVC, exact-length routing edges).

---

## AI tooling

I used GitHub Copilot (chat + inline completions) as an assistant while building
this. Concretely:

- **Scaffolding & boilerplate**: generating the initial Page Object classes,
  the `requests` client method signatures, and the pytest fixture skeletons,
  which I then edited to fit the documented contract.
- **Test-case brainstorming**: suggesting negative/boundary cases (short routing,
  over-length account, Luhn-fail card, past expiry) — I picked the representative
  subset rather than keeping everything it proposed.
- **Luhn helper**: drafting the mod-10 checksum, which I sanity-checked against a
  known-valid test card.
- **README polish**: tightening wording and formatting.

What I verified by hand:

- I inspected the UI elements directly, debugged the flows against the real     
  application, and exercised the APIs in Postman before automating them.
- Read the API Docs myself and reconciled the real endpoint
  paths, request field names (`email`, `exp_month`/`exp_year`), and response
  schemas (`routing_masked`, `account_masked`, `last4`, …) against the code —
  Copilot's first guesses didn't always match.
- Confirmed the two-step `auth/token` → `auth/mfa/verify` flow and the `1234`
  MFA code from the docs, not from AI output.
- Reasoned through the cross-layer assertion (comparing masked last-4 across API
  and UI) and the security checks (no PAN/CVC/account leakage on error) myself —
  this is the core of the challenge and not something I delegated.
- Ran the suite locally and fixed the mismatches AI introduced (e.g. selector and
  field-name assumptions) rather than trusting generated code as-is.