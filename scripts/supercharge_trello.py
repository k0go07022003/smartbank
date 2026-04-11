"""Upgrade the existing SmartBank Trello board with a richer UX.

What this adds on top of ``setup_trello.py``:

* Colored **card covers** based on priority (Critical/High/Medium)
* **Checklists** — every FR/NFR/UC acceptance criterion becomes a
  subtask; on completed cards we auto-tick the boxes so you can see
  100 % filled bars.
* **Due dates** derived from the Quest2&3.docx milestone plan
  (M1..M5, February–June 2026).
* **GitHub links** in the card description pointing at the exact
  module/function that implements the item.
* **Activity comments** announcing completion.
* **Board background** set to a dark blue.
* **Emoji prefixes** on every card name for a visual scan.
"""
import os
import sys
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


def get(path, **p): return req("GET", path, **p)
def post(path, **p): return req("POST", path, **p)
def put(path, **p): return req("PUT", path, **p)


# ---------- configuration ----------

EMOJI = {
    "FR-01": "👤", "FR-02": "🔐", "FR-03": "💳", "FR-04": "📜",
    "FR-05": "💸", "FR-06": "🏦", "FR-07": "✏️", "FR-08": "🔔",
    "FR-09": "🛠️", "FR-10": "🚫",
    "NFR-01": "🛡️", "NFR-02": "⚡", "NFR-03": "💾",
    "NFR-04": "🎨", "NFR-05": "📈", "NFR-06": "🌍",
    "UC-01": "📝", "UC-02": "💱", "UC-03": "👮",
    "R1": "🧩", "R2": "🔓", "R3": "📚", "R4": "⏰",
    "R5": "📢", "R6": "🔄", "R7": "🗑️",
}

COVER_COLOR = {
    "Critical": "red",
    "High": "orange",
    "Medium": "yellow",
    "Low": "sky",
}

# (name prefix, priority, due-date-ISO or None, github link, checklist items)
CARDS = {
    "FR-01 User Registration": (
        "High", "2026-05-10",
        "app/models.py#L26-L45  (register_user)",
        [
            ("Password min 6 chars", True),
            ("Email unique and well-formed", True),
            ("Default account opened on registration", True),
            ("Unit test: test_register_creates_user_and_default_account", True),
            ("HTTP test: test_register_and_login_flow", True),
        ],
    ),
    "FR-02 User Authentication": (
        "High", "2026-05-10",
        "app/models.py#L48-L55  (authenticate)",
        [
            ("Valid credentials grant access", True),
            ("Invalid credentials rejected", True),
            ("Blocked accounts cannot log in", True),
            ("Session cleared on logout", True),
            ("login_required decorator on protected routes", True),
        ],
    ),
    "FR-03 Account Overview": (
        "High", "2026-05-15",
        "app/routes.py  (/dashboard)",
        [
            ("Dashboard shows account number, balance, status", True),
            ("Supports multiple accounts per user", True),
            ("Modern glassmorphism gradient card UI", True),
            ("HTTP test: test_dashboard_shows_balance", True),
        ],
    ),
    "FR-04 Transaction History": (
        "Medium", "2026-05-20",
        "app/models.py  (transaction_history)",
        [
            ("Sorted newest first", True),
            ("Shows date, type, amount, description", True),
            ("Covers source AND destination account", True),
            ("Unit test: test_transaction_history_contains_all", True),
        ],
    ),
    "FR-05 Money Transfer": (
        "High", "2026-05-20",
        "app/models.py  (transfer)",
        [
            ("Sender balance decreases", True),
            ("Recipient balance increases", True),
            ("Insufficient funds blocked", True),
            ("Same-account transfer blocked", True),
            ("Unknown recipient blocked", True),
            ("Both users notified", True),
            ("5 unit tests passing", True),
        ],
    ),
    "FR-06 Deposits and Withdrawals": (
        "High", "2026-05-15",
        "app/models.py  (deposit/withdraw)",
        [
            ("Deposit increases balance", True),
            ("Withdraw blocked on insufficient funds", True),
            ("Amount must be positive", True),
            ("Notifications emitted", True),
        ],
    ),
    "FR-07 Profile Management": (
        "Medium", "2026-05-25",
        "app/models.py  (update_profile)",
        [
            ("Update full_name, email, phone, address", True),
            ("None fields skipped (partial update)", True),
            ("HTTP test: test_profile_update", True),
        ],
    ),
    "FR-08 Notifications": (
        "Medium", "2026-05-25",
        "app/models.py  (_notify)",
        [
            ("Every tx creates a notification row", True),
            ("Dashboard shows 5 most recent", True),
            ("Full list at /notifications", True),
            ("Observer pattern (pub-sub via DB)", True),
        ],
    ),
    "FR-09 Administrative Panel": (
        "Medium", "2026-05-30",
        "app/routes.py  (/admin)",
        [
            ("admin_required decorator (403 for customers)", True),
            ("Shows user list", True),
            ("Shows recent transactions", True),
            ("HTTP test: test_customer_cannot_access_admin", True),
        ],
    ),
    "FR-10 Account Management by Administrator": (
        "Medium", "2026-05-30",
        "app/models.py  (set_user_status)",
        [
            ("Block status cascades to user accounts", True),
            ("Audit log entry written", True),
            ("Blocked user cannot log in", True),
            ("HTTP test: test_admin_login_and_block_user", True),
        ],
    ),
    "NFR-01 Security": (
        "Critical", "2026-06-01",
        "app/models.py  (generate_password_hash pbkdf2)",
        [
            ("pbkdf2-sha256 password hashing", True),
            ("Role-based access control (customer/admin)", True),
            ("Parameterized SQL everywhere", True),
            ("HTTPS in production (TODO: cert on deploy)", False),
            ("OWASP audit", False),
        ],
    ),
    "NFR-02 Performance": (
        "High", "2026-06-05",
        "app/db.py  (per-request SQLite connection)",
        [
            ("<2s response on local ops", True),
            ("Load test for 100 concurrent users", False),
            ("DB indices review", False),
        ],
    ),
    "NFR-03 Reliability": (
        "High", "2026-06-05",
        "app/models.py  (transactional updates)",
        [
            ("Transactional updates with rollback", True),
            ("Graceful DomainError/AuthError handling", True),
            ("Automated daily backups", False),
            ("99.5% uptime SLO doc", False),
        ],
    ),
    "NFR-04 Usability": (
        "Medium", "2026-06-05",
        "app/static/style.css  (responsive UI)",
        [
            ("Intuitive navigation", True),
            ("Responsive on mobile", True),
            ("WCAG 2.1 AA audit", False),
        ],
    ),
    "NFR-05 Scalability": (
        "Medium", "2026-06-10",
        "app/__init__.py  (Flask blueprints)",
        [
            ("Blueprint-based routing", True),
            ("Repository layer (models.py) decoupled", True),
            ("DB migration strategy (TODO: alembic)", False),
        ],
    ),
    "NFR-06 Compatibility": (
        "Medium", "2026-06-05",
        "app/templates/base.html  (responsive viewport)",
        [
            ("Works on Chrome", True),
            ("Works on Firefox", True),
            ("Works on Safari", True),
            ("Mobile responsive", True),
        ],
    ),
    "UC-01 User Registration": (
        "High", "2026-05-10",
        "app/routes.py  (register view)",
        [
            ("Registration page renders", True),
            ("Validation on empty/invalid input", True),
            ("Success redirect to login", True),
            ("Error path on duplicate email", True),
        ],
    ),
    "UC-02 Money Transfer": (
        "High", "2026-05-20",
        "app/routes.py  (transfer view)",
        [
            ("Transfer form with source/dest/amount", True),
            ("Server-side balance validation", True),
            ("Transaction record created", True),
            ("Notification sent to both parties", True),
            ("OTP flow (TODO — out of scope for MVP)", False),
        ],
    ),
    "UC-03 Account Management by Administrator": (
        "Medium", "2026-05-30",
        "app/routes.py  (admin_set_status)",
        [
            ("Admin dashboard with user list", True),
            ("Block / unblock actions", True),
            ("Audit log written", True),
        ],
    ),
    "R1 Integration complexity": (
        "High", None,
        "Flask all-in-one (no frontend split)",
        [
            ("Monolithic reduces integration risk", True),
            ("29 tests cover integration", True),
        ],
    ),
    "R2 Security vulnerabilities": (
        "Critical", None,
        "app/models.py, app/routes.py",
        [
            ("Parameterized queries everywhere", True),
            ("Password hashing (pbkdf2)", True),
            ("Pre-deploy OWASP audit", False),
        ],
    ),
    "R3 Technology learning curve": (
        "Medium", None, "Flask/SQLite — well-known stack",
        [("Flask already familiar", True)],
    ),
    "R4 Schedule delays": (
        "High", None, "Project schedule M1-M5",
        [
            ("Weekly progress meetings", False),
            ("Buffer time in schedule", True),
        ],
    ),
    "R5 Communication gaps": (
        "Medium", None, "Trello + GitHub + docs",
        [
            ("Trello board live", True),
            ("GitHub as single source of truth", True),
        ],
    ),
    "R6 Changing requirements": (
        "Medium", None, "Agile iterative approach",
        [
            ("Blueprint-based architecture", True),
            ("Change log in git history", True),
        ],
    ),
    "R7 Data loss": (
        "Critical", None, "Git + GitHub",
        [
            ("Git with GitHub remote", True),
            ("Automated daily DB backup", False),
        ],
    ),
}

# Cards that should be announced as "Completed" via a comment
COMPLETED = {k for k, v in CARDS.items()
             if all(done for _, done in v[3])}


# ---------- operations ----------

def find_board(name="SmartBank"):
    for b in get("/members/me/boards", fields="name"):
        if b["name"] == name:
            return b["id"]
    sys.exit("board not found")


def set_background(board_id):
    """Set the board background to a dark navy."""
    try:
        put(f"/boards/{board_id}", **{
            "prefs/background": "blue",
        })
        print("  * background set")
    except Exception as e:
        print(f"  ! background: {e}")


def rename_with_emoji(card_id, current_name):
    """Prefix the card name with an appropriate emoji if not already."""
    for key, emoji in EMOJI.items():
        if current_name.startswith(key):
            new_name = f"{emoji} {current_name}"
            # skip if already prefixed
            if current_name[0] in "👤🔐💳📜💸🏦✏️🔔🛠️🚫🛡️⚡💾🎨📈🌍📝💱👮🧩🔓📚⏰📢🔄🗑️":
                return
            put(f"/cards/{card_id}", name=new_name)
            return


def set_cover(card_id, color):
    """Set a colored cover strip on the card."""
    import json
    put(f"/cards/{card_id}", cover=json.dumps({
        "color": color,
        "size": "normal",
        "brightness": "dark",
    }))


def append_description(card_id, current_desc, github_link):
    link = f"{REPO}/{github_link.split()[0].split('#')[0]}"
    extra = f"\n\n---\n**📎 Implementation:** [`{github_link}`]({link})"
    if github_link in (current_desc or ""):
        return
    put(f"/cards/{card_id}", desc=(current_desc or "") + extra)


def add_checklist(card_id, card_name, items):
    """Create a 'Acceptance criteria' checklist with ticked items."""
    # skip if already has one with this name
    existing = get(f"/cards/{card_id}/checklists")
    if any(c["name"] == "Acceptance criteria" for c in existing):
        return
    cl = post(f"/cards/{card_id}/checklists", name="Acceptance criteria")
    for text, done in items:
        item = post(f"/checklists/{cl['id']}/checkItems",
                    name=text,
                    checked="true" if done else "false")
        # Setting state=complete after creation is sometimes required
        if done:
            try:
                put(f"/cards/{card_id}/checkItem/{item['id']}",
                    state="complete")
            except Exception:
                pass


def set_due(card_id, due_iso):
    if due_iso is None:
        return
    put(f"/cards/{card_id}", due=f"{due_iso}T12:00:00.000Z",
        dueComplete="true")


def add_completion_comment(card_id, card_name):
    comments = get(f"/cards/{card_id}/actions", filter="commentCard")
    if any("Completed" in a["data"]["text"] for a in comments):
        return
    post(f"/cards/{card_id}/actions/comments",
         text=f"✅ Completed — all acceptance criteria met. "
              f"See commit history on GitHub for details.")


def process_card(card, board_id):
    name = card["name"]
    # find the entry by its original prefix
    for key, payload in CARDS.items():
        if name == key or name.endswith(key):
            prio, due, gh, items = payload
            try:
                rename_with_emoji(card["id"], name)
                set_cover(card["id"], COVER_COLOR[prio])
                append_description(card["id"], card.get("desc", ""), gh)
                add_checklist(card["id"], name, items)
                set_due(card["id"], due)
                if key in COMPLETED:
                    add_completion_comment(card["id"], name)
                return f"✓ {name}"
            except Exception as e:
                return f"✗ {name}: {e}"
    return f"- skipped {name}"


def main():
    board_id = find_board()
    print(f"board: {board_id}")

    print("background:")
    set_background(board_id)

    print("cards:")
    cards = get(f"/boards/{board_id}/cards", fields="name,desc")

    # Run in parallel — Trello API handles it fine in small bursts
    with ThreadPoolExecutor(max_workers=4) as ex:
        futures = [ex.submit(process_card, c, board_id) for c in cards]
        for f in as_completed(futures):
            print(f"  {f.result()}")

    print(f"\ndone. https://trello.com/b/{board_id}")


if __name__ == "__main__":
    main()
