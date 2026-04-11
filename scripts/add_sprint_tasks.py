"""Add concrete sprint tasks to the SmartBank Trello board.

``setup_trello.py`` creates cards for the high-level requirements
(FR/NFR/UC/Risk). This script adds the **work items** a real team
would track during development — implementation tasks, testing
tasks, DevOps, documentation, UX work — each with a description,
acceptance criteria checklist, priority cover, due date and GitHub
link. Cards are placed in the right Kanban column based on their
current status.
"""
import os
import sys
import json
import time
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed

API = "https://api.trello.com/1"
KEY = os.environ["TRELLO_KEY"]
TOKEN = os.environ["TRELLO_TOKEN"]
AUTH = {"key": KEY, "token": TOKEN}

REPO = "https://github.com/k0go07022003/smartbank/blob/main"


def req(method, path, **params):
    r = requests.request(method, f"{API}{path}",
                         params={**AUTH, **params})
    r.raise_for_status()
    return r.json() if r.content else {}


def get(p, **k): return req("GET", p, **k)
def post(p, **k): return req("POST", p, **k)
def put(p, **k): return req("PUT", p, **k)


COVER = {"Critical": "red", "High": "orange",
         "Medium": "yellow", "Low": "sky"}


# ---------- task catalog ----------
#
# schema: (title, emoji, column, priority, due, description, checklist, github)
# column must be one of: Backlog / To Do / In Progress / In Review / Done

TASKS = [
    # ========== Sprint 1: foundation (DONE) ==========
    ("Project scaffold & git init", "🏗️", "Done", "High", "2026-04-01",
     "Bootstrap the Flask project layout, create the virtualenv, init git repo, "
     "write the application factory and SQLite schema.",
     [
         ("Flask application factory in app/__init__.py", True),
         ("SQLite schema (users/accounts/transactions/notifications/audit_log)", True),
         ("Per-request DB connection on flask.g", True),
         ("run.py entry point", True),
         ("requirements.txt pinned", True),
         (".gitignore configured", True),
     ],
     "app/__init__.py"),

    ("Domain layer: models.py", "🧠", "Done", "High", "2026-04-05",
     "Implement the business logic layer. Routes must never touch SQL "
     "directly — everything goes through models.py functions.",
     [
         ("register_user + open_account", True),
         ("authenticate with pbkdf2-sha256", True),
         ("deposit / withdraw with validation", True),
         ("transfer with balance checks + dual notification", True),
         ("transaction_history for an account", True),
         ("Admin: list_users, set_user_status (cascading)", True),
         ("DomainError / AuthError custom exceptions", True),
     ],
     "app/models.py"),

    ("HTTP layer: routes.py + blueprints", "🌐", "Done", "High", "2026-04-08",
     "Wire the URL map — register/login/logout, dashboard, "
     "deposit/withdraw/transfer, admin panel, JSON API.",
     [
         ("Auth routes (register/login/logout)", True),
         ("Dashboard + account detail", True),
         ("Deposit/withdraw/transfer forms", True),
         ("Profile + notifications pages", True),
         ("Admin panel (users + transactions)", True),
         ("JSON API: /api/accounts, /api/transactions/<num>", True),
         ("@login_required and @admin_required decorators", True),
     ],
     "app/routes.py"),

    ("Jinja2 templates + base layout", "🎨", "Done", "Medium", "2026-04-10",
     "Create 10 server-rendered templates extending a shared base.html "
     "with flash messages and navigation.",
     [
         ("base.html with nav and flashes", True),
         ("login.html + register.html", True),
         ("dashboard.html with account cards", True),
         ("account.html with history table", True),
         ("deposit/withdraw/transfer forms", True),
         ("profile.html + notifications.html", True),
         ("admin.html with user management", True),
     ],
     "app/templates/base.html"),

    ("Modern fintech UI (CSS)", "💅", "Done", "Medium", "2026-04-10",
     "Glassmorphism dark theme with gradient credit cards, Inter font, "
     "subtle animations, responsive layout.",
     [
         ("Gradient account cards with chip graphic", True),
         ("Glassmorphism panels with backdrop-blur", True),
         ("Inter + JetBrains Mono typography", True),
         ("Animated flash messages (slideDown)", True),
         ("Responsive @media queries", True),
         ("Custom scrollbar styling", True),
     ],
     "app/static/style.css"),

    # ========== Sprint 2: testing (DONE) ==========
    ("Pytest fixtures + test infrastructure", "🧪", "Done", "High", "2026-04-11",
     "Create reusable fixtures (app, client, alice, bob) with an "
     "isolated per-test SQLite file.",
     [
         ("conftest.py with app/client fixtures", True),
         ("Seeded alice (1000 PLN) and bob (0 PLN) fixtures", True),
         ("Isolated tempfile DB per test", True),
         ("_login() helper for session setup", True),
     ],
     "tests/conftest.py"),

    ("Unit tests for domain logic", "🔬", "Done", "High", "2026-04-11",
     "16 unit tests covering models.py happy paths and edge cases.",
     [
         ("Register: happy path, short pwd, duplicate", True),
         ("Authenticate: ok, wrong pwd, blocked", True),
         ("Deposit: increase, reject negative", True),
         ("Withdraw: decrease, insufficient funds", True),
         ("Transfer: move, same-acct, insufficient, unknown dst", True),
         ("History + notifications", True),
         ("Admin block cascades to accounts", True),
         ("Update profile partial", True),
     ],
     "tests/test_models.py"),

    ("Integration tests for HTTP layer", "🔗", "Done", "High", "2026-04-11",
     "13 end-to-end tests driving the Flask test client.",
     [
         ("Register → login flow", True),
         ("Login required redirect", True),
         ("Dashboard balance render", True),
         ("Transfer via HTTP + insufficient error", True),
         ("Deposit/withdraw endpoints", True),
         ("Profile update", True),
         ("Customer cannot access /admin (403)", True),
         ("Admin blocks user → login fails", True),
         ("JSON API returns accounts", True),
         ("Cannot view other user's account (404)", True),
     ],
     "tests/test_routes.py"),

    # ========== Sprint 3: documentation (DONE) ==========
    ("README with setup and traceability", "📘", "Done", "Medium", "2026-04-11",
     "Project README with setup instructions, project structure, "
     "API endpoint table, and requirements traceability matrix.",
     [
         ("Quick start section", True),
         ("Architecture ASCII diagram", True),
         ("API endpoint table", True),
         ("FR/NFR → code traceability matrix", True),
         ("Screenshots (TODO — add after deploy)", False),
     ],
     "README.md"),

    ("DESIGN_PATTERNS catalog (MD + PDF)", "🏛️", "Done", "Medium", "2026-04-11",
     "Catalogue of 8 design patterns actually used in the codebase, "
     "with motivation, code location and 'why not' section for "
     "patterns we deliberately rejected.",
     [
         ("Application Factory", True),
         ("Repository / Data Access Module", True),
         ("Template Method (Transaction hierarchy)", True),
         ("Observer / Pub-Sub for notifications", True),
         ("Decorator (login_required, admin_required)", True),
         ("Front Controller + Blueprint", True),
         ("Per-request Singleton (flask.g)", True),
         ("PDF rendered with reportlab", True),
     ],
     "DESIGN_PATTERNS.md"),

    ("pdoc HTML API docs generated", "📖", "Done", "Medium", "2026-04-11",
     "Auto-generated API documentation from docstrings (lab14 "
     "requirement).",
     [
         ("Docstrings on all public functions", True),
         ("pdoc3 html output in docs/app/", True),
         ("Cross-references to FR-xx requirement IDs", True),
     ],
     "docs/app/index.html"),

    # ========== Sprint 4: Scrum / process (DONE) ==========
    ("Trello board provisioning", "📋", "Done", "Medium", "2026-04-11",
     "Programmatic Trello setup for lab07 — board, lists, labels, "
     "FR/NFR/UC/Risk cards generated from Quest2&3 spec.",
     [
         ("setup_trello.py idempotent provisioning", True),
         ("sync_trello_progress.py to reflect current state", True),
         ("supercharge_trello.py covers/checklists/due dates", True),
         ("add_sprint_tasks.py (this script)", True),
     ],
     "scripts/setup_trello.py"),

    # ========== Sprint 5: hardening (IN PROGRESS / REVIEW) ==========
    ("Load test with 100 concurrent users", "🚦", "To Do", "High", "2026-05-15",
     "NFR-02 acceptance criterion. Use locust or k6 to verify the "
     "system meets the <2s response time under 100 concurrent users.",
     [
         ("Install locust", False),
         ("Write locustfile with login + dashboard + transfer flow", False),
         ("Run 100 users / 10 req/s for 5 minutes", False),
         ("Record p50/p95/p99 latency", False),
         ("Document results in test_reports/", False),
     ],
     "tests/"),

    ("OWASP security audit checklist", "🛡️", "To Do", "Critical", "2026-05-20",
     "Walk through OWASP Top 10 against the SmartBank codebase and "
     "file findings as new cards where needed. Required for NFR-01 "
     "and risk R2 mitigation.",
     [
         ("A01 Broken access control — review decorators", False),
         ("A02 Cryptographic failures — hashing review", False),
         ("A03 Injection — confirm parameterised queries", False),
         ("A04 Insecure design — threat model", False),
         ("A05 Security misconfig — review secret key", False),
         ("A07 Identification & auth failures — session review", False),
         ("A09 Logging failures — audit log review", False),
         ("Fill SECURITY.md report", False),
     ],
     "app/models.py"),

    ("OTP verification for money transfers", "📱", "Backlog", "High", "2026-05-25",
     "UC-02 specifies OTP verification for transfers. Out of scope "
     "for MVP, planned for Sprint 5. Use pyotp with a 6-digit TOTP "
     "displayed in the UI (stand-in for SMS).",
     [
         ("Add otp_secret column to users table", False),
         ("Generate secret on registration", False),
         ("Show QR code for authenticator apps", False),
         ("Verify OTP before committing transfer", False),
         ("3 retries then block the transaction", False),
         ("Unit tests for OTP happy/retry/block paths", False),
     ],
     "app/models.py"),

    ("Email notifications via SMTP", "📧", "Backlog", "Medium", "2026-05-30",
     "FR-08 currently only creates in-app notifications. Add an "
     "email channel for important events (login from new device, "
     "large transfers).",
     [
         ("SMTP config in instance/", False),
         ("NotificationChannel abstraction (Strategy pattern)", False),
         ("EmailChannel implementation using smtplib", False),
         ("Configurable threshold for 'large transfer'", False),
         ("Template rendering with Jinja2", False),
         ("Retry with exponential backoff on SMTP errors", False),
     ],
     "app/models.py"),

    ("Admin dashboard charts", "📊", "Backlog", "Medium", "2026-06-01",
     "Visual analytics on the admin panel: daily transaction "
     "volume, user growth, top accounts by balance.",
     [
         ("Chart.js from CDN", False),
         ("Endpoint /admin/api/stats returning JSON", False),
         ("Daily tx count chart (last 30 days)", False),
         ("User growth chart", False),
         ("Top 10 accounts table", False),
     ],
     "app/routes.py"),

    ("Docker containerization", "🐳", "To Do", "Medium", "2026-05-20",
     "Multi-stage Dockerfile + docker-compose for local dev and "
     "staging deployment. Addresses R1 (integration complexity).",
     [
         ("Dockerfile with python:3.12-slim", False),
         ("gunicorn as production WSGI server", False),
         ("docker-compose.yml with volume for sqlite", False),
         ("Healthcheck endpoint /health", False),
         ("Image size < 200 MB", False),
     ],
     "Dockerfile"),

    ("GitHub Actions CI pipeline", "⚙️", "To Do", "High", "2026-05-12",
     "Run pytest on every push. Add a coverage badge to the README.",
     [
         (".github/workflows/ci.yml", False),
         ("Install Python + pip cache", False),
         ("Run pytest with coverage", False),
         ("Upload coverage to Codecov", False),
         ("Badge in README", False),
         ("Fail PR on test regression", False),
     ],
     ".github/workflows/"),

    ("Automated daily SQLite backup", "💾", "Backlog", "High", "2026-06-05",
     "NFR-03 reliability: daily backup of instance/smartbank.sqlite "
     "to a timestamped file with 30-day retention.",
     [
         ("backup.sh script using sqlite3 .backup", False),
         ("cron job (or systemd timer)", False),
         ("30-day rotation", False),
         ("Restore procedure documented", False),
     ],
     "scripts/"),

    ("Structured logging with request IDs", "📑", "Backlog", "Medium", "2026-06-05",
     "Replace print/default Flask logging with structured JSON logs. "
     "Each request carries a correlation ID written into audit_log.",
     [
         ("structlog config", False),
         ("Request ID middleware", False),
         ("Correlation ID on domain events", False),
         ("Log file rotation", False),
     ],
     "app/__init__.py"),

    ("WCAG 2.1 AA accessibility audit", "♿", "In Review", "Medium", "2026-06-05",
     "NFR-04 acceptance: new users complete core tasks unaided, "
     "interface meets WCAG 2.1 AA.",
     [
         ("Color contrast ratios measured", True),
         ("Keyboard navigation tested", True),
         ("Form labels and ARIA attributes", True),
         ("Screen reader pass (VoiceOver)", False),
         ("axe-core automated scan", False),
     ],
     "app/templates/"),

    ("Database migration tool (alembic)", "🗄️", "Backlog", "Low", "2026-06-10",
     "Replace the 'CREATE TABLE IF NOT EXISTS' bootstrap with proper "
     "migrations so schema changes become reviewable.",
     [
         ("Install alembic", False),
         ("Initial migration matches current schema", False),
         ("CI check that migrations are up to date", False),
         ("Rollback procedure documented", False),
     ],
     "app/db.py"),

    ("User manual (PL + EN)", "📕", "Backlog", "Medium", "2026-06-12",
     "End-user documentation for customers and admins. Lab14 "
     "deliverable.",
     [
         ("Customer guide: register / login / transfer", False),
         ("Admin guide: block user / review tx", False),
         ("Screenshots from live deployment", False),
         ("FAQ section", False),
         ("PDF export via pandoc or reportlab", False),
     ],
     "docs/"),

    ("User acceptance testing (UAT) session", "🧑‍🔬", "Backlog", "High", "2026-06-12",
     "Run a UAT session with 3 volunteer users walking through the "
     "main flows. Record findings, file bugs.",
     [
         ("Recruit 3 external testers", False),
         ("Prepare scenario script", False),
         ("Live observation + note taking", False),
         ("Bug triage after session", False),
         ("UAT report committed to docs/", False),
     ],
     "docs/"),

    ("Final deployment to staging", "🚀", "Backlog", "Critical", "2026-06-14",
     "Ship the tested application to a public staging server "
     "(M5 deliverable).",
     [
         ("Choose host (Fly.io / Render / Railway)", False),
         ("TLS certificate via Let's Encrypt", False),
         ("Environment variables for SECRET_KEY", False),
         ("Admin password rotated from default", False),
         ("Smoke test on production URL", False),
     ],
     "run.py"),

    # ========== Bugs / chores ==========
    ("BUG: scrypt unavailable on macOS Python 3.9", "🐛", "Done", "Medium", "2026-04-11",
     "Default werkzeug password hasher uses scrypt which is not "
     "compiled in on the macOS system Python. Switched to "
     "pbkdf2:sha256 which is available everywhere.",
     [
         ("Reproduce the failure in test run", True),
         ("Switch to pbkdf2:sha256 in models.py", True),
         ("29 tests green", True),
     ],
     "app/models.py"),

    ("CHORE: upgrade Python to 3.12 in dev", "🔧", "Backlog", "Low", "2026-05-01",
     "System Python 3.9 misses hashlib.scrypt and other modern "
     "features. Install 3.12 via pyenv and pin in .python-version.",
     [
         ("pyenv install 3.12", False),
         (".python-version committed", False),
         ("Verify all tests pass on 3.12", False),
     ],
     None),

    # ========== Scrum ceremonies ==========
    ("Sprint planning — Sprint 5 kickoff", "🏃", "To Do", "High", "2026-05-12",
     "Planning meeting for sprint 5 (hardening & security). "
     "Confirm scope with the team, estimate stories.",
     [
         ("Review Sprint 4 velocity", False),
         ("Pick stories from Backlog", False),
         ("Estimate in story points", False),
         ("Commit to sprint goal", False),
     ],
     None),

    ("Daily standups — async via Discord", "☕", "In Progress", "Low", "2026-05-12",
     "Each team member posts yesterday / today / blockers in the "
     "#smartbank Discord channel every morning.",
     [
         ("Channel created", True),
         ("Template pinned", True),
         ("Daily cadence maintained", False),
     ],
     None),

    ("Sprint retro after Sprint 4", "🔍", "To Do", "Medium", "2026-05-10",
     "What went well / what didn't / what to try next. Lab07 "
     "Scrum ceremonies.",
     [
         ("Gather 'went well' points", False),
         ("Gather 'didn't go well' points", False),
         ("Decide 2 experiments for next sprint", False),
         ("Post retro notes to Trello", False),
     ],
     None),
]


# ---------- helpers ----------

def find_board(name="SmartBank"):
    for b in get("/members/me/boards", fields="name"):
        if b["name"] == name:
            return b["id"]
    sys.exit("board not found — run setup_trello.py first")


def list_cards(board_id):
    return {c["name"].split("] ", 1)[-1]: c  # strip emoji prefix if present
            for c in get(f"/boards/{board_id}/cards", fields="name")}


def create_card(list_id, title, emoji, priority, due, desc,
                checklist, github):
    name = f"{emoji} {title}"
    body = desc
    if github:
        body += f"\n\n---\n**📎 Code:** [`{github}`]({REPO}/{github})"

    card = post("/cards",
                idList=list_id,
                name=name,
                desc=body,
                pos="bottom")

    # cover color
    try:
        put(f"/cards/{card['id']}", cover=json.dumps({
            "color": COVER[priority],
            "size": "normal",
            "brightness": "dark",
        }))
    except Exception as e:
        print(f"    ! cover {name}: {e}")

    # checklist
    if checklist:
        cl = post(f"/cards/{card['id']}/checklists",
                  name="Acceptance criteria")
        for text, done in checklist:
            item = post(f"/checklists/{cl['id']}/checkItems",
                        name=text,
                        checked="true" if done else "false")
            if done:
                try:
                    put(f"/cards/{card['id']}/checkItem/{item['id']}",
                        state="complete")
                except Exception:
                    pass

    # due date
    if due:
        try:
            done_flag = ("true"
                         if all(d for _, d in checklist)
                         else "false")
            put(f"/cards/{card['id']}",
                due=f"{due}T12:00:00.000Z",
                dueComplete=done_flag)
        except Exception as e:
            print(f"    ! due {name}: {e}")

    return f"✓ {emoji} {title}"


def process_task(task, board_id, list_ids, existing_titles):
    title = task[0]
    if title in existing_titles:
        return f"- skipped (exists) {title}"
    (_, emoji, column, priority, due, desc, checklist, github) = task
    try:
        return create_card(list_ids[column], title, emoji, priority,
                           due, desc, checklist, github)
    except Exception as e:
        return f"✗ {title}: {e}"


def main():
    board_id = find_board()
    print(f"board: {board_id}")

    list_ids = {l["name"]: l["id"] for l in get(f"/boards/{board_id}/lists")}
    print(f"lists: {list(list_ids)}")

    # Build set of existing card titles (strip emoji prefix)
    existing_titles = set()
    for c in get(f"/boards/{board_id}/cards", fields="name"):
        # strip leading emoji + space
        name = c["name"]
        # walk past any emoji characters
        i = 0
        while i < len(name) and not name[i].isalnum():
            i += 1
        existing_titles.add(name[i:].strip())

    print(f"{len(TASKS)} tasks to add / verify")

    with ThreadPoolExecutor(max_workers=4) as ex:
        futures = [ex.submit(process_task, t, board_id, list_ids,
                             existing_titles)
                   for t in TASKS]
        for f in as_completed(futures):
            print(f"  {f.result()}")

    print(f"\ndone. https://trello.com/b/{board_id}")


if __name__ == "__main__":
    main()
