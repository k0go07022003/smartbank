# SmartBank — Bank Account Management System

Academic project for **Software Engineering** course (Inżynieria Oprogramowania).
A secure, lightweight banking web application built with Flask + SQLite.

**Team:** Daniel Bober (PM, Backend) · Kamil Bialik (Frontend, UX) · Szymon Adamek (DBA, QA)

---

## Features

- 🔐 User registration & authentication (pbkdf2-SHA256 hashed passwords)
- 💳 Multi-account dashboard with live balances
- 💸 Deposits, withdrawals, and inter-account transfers with balance validation
- 📜 Transaction history per account
- 🔔 In-app notifications on every transaction
- 👤 Profile management
- 🛠️ Administrator panel: block/unblock users, audit log, transactions overview
- 🔌 JSON API endpoints (`/api/accounts`, `/api/transactions/<num>`)

## Architecture

```
┌─────────────┐     HTTP      ┌──────────────┐     SQL     ┌─────────┐
│  Browser    │ ────────────▶ │   Flask App  │ ──────────▶ │ SQLite  │
│ (Jinja UI)  │ ◀──────────── │  (factory)   │ ◀────────── │   DB    │
└─────────────┘  rendered HTML└──────┬───────┘             └─────────┘
                                     │
                        ┌────────────┴────────────┐
                        ▼                         ▼
                 ┌────────────┐           ┌──────────────┐
                 │ routes.py  │           │  models.py   │
                 │ (controllers)│──uses──▶│ (domain ops) │
                 └────────────┘           └──────────────┘
```

## Project structure

```
smartbank/
├── app/
│   ├── __init__.py         # Flask application factory + admin seed
│   ├── db.py               # SQLite connection and schema bootstrap
│   ├── models.py           # Domain operations (User/Account/Transaction/Notification)
│   ├── routes.py           # HTTP routes (controllers) + JSON API
│   ├── static/style.css    # Glassmorphism UI
│   └── templates/          # Jinja2 templates
│       ├── base.html
│       ├── login.html / register.html
│       ├── dashboard.html
│       ├── account.html
│       ├── deposit.html / withdraw.html / transfer.html
│       ├── profile.html / notifications.html
│       └── admin.html
├── tests/
│   ├── conftest.py         # pytest fixtures (app, client, alice, bob)
│   ├── test_models.py      # Unit tests (16)
│   └── test_routes.py      # Integration tests (13)
├── docs/                   # Generated HTML docs (pdoc)
├── DESIGN_PATTERNS.md      # Design patterns catalog
├── requirements.txt
├── run.py                  # Entry point
└── README.md
```

## Quick start

```bash
# 1. Install dependencies
pip3 install -r requirements.txt

# 2. Run the server
python3 run.py

# 3. Open http://127.0.0.1:5050 in your browser
```

### Default credentials

- **Admin:** `admin` / `admin123`
- Or register a new customer at `/register`

## Running tests

```bash
PYTHONPATH=. python3 -m pytest -v
```

Expected: **29 passed** (16 unit + 13 integration)

## API endpoints

| Method | Path | Description |
|---|---|---|
| GET/POST | `/register` | Create customer account (auto-opens one bank account) |
| GET/POST | `/login` | Authenticate |
| GET | `/logout` | Clear session |
| GET | `/dashboard` | Customer dashboard |
| GET | `/account/<account_number>` | Account details + history |
| GET/POST | `/deposit` | Deposit funds |
| GET/POST | `/withdraw` | Withdraw funds |
| GET/POST | `/transfer` | Inter-account transfer |
| GET/POST | `/profile` | View/update profile |
| GET | `/notifications` | In-app notifications list |
| GET | `/admin` | Admin-only: users + transactions |
| POST | `/admin/user/<id>/status` | Admin-only: block/unblock |
| GET | `/api/accounts` | JSON list of current user's accounts |
| GET | `/api/transactions/<num>` | JSON transaction history |

## Requirements traceability

| Spec | ID | Where |
|---|---|---|
| Registration | FR-01 | `models.register_user`, `/register` |
| Authentication | FR-02 | `models.authenticate`, `/login` |
| Account Overview | FR-03 | `/dashboard`, `models.get_accounts` |
| Transaction History | FR-04 | `/account/<num>`, `models.transaction_history` |
| Money Transfer | FR-05 | `models.transfer`, `/transfer` |
| Deposits/Withdrawals | FR-06 | `models.deposit/withdraw`, `/deposit`, `/withdraw` |
| Profile Management | FR-07 | `models.update_profile`, `/profile` |
| Notifications | FR-08 | `models._notify`, `/notifications` |
| Admin Panel | FR-09 | `/admin` |
| Account Management | FR-10 | `models.set_user_status`, `/admin/user/<id>/status` |
| Security | NFR-01 | pbkdf2-sha256 hashing, role-based access, parameterized SQL |
| Performance | NFR-02 | SQLite with indices, sub-100ms response on local ops |
| Reliability | NFR-03 | Transactional updates, rollback on error |

See `DESIGN_PATTERNS.md` for the patterns catalog.

## Generating API docs

```bash
pip3 install pdoc
pdoc --html --output-dir docs app
```

Open `docs/app/index.html`.

## License

Academic use only.
