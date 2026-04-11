"""Provision the SmartBank Scrum board on Trello.

Usage
-----
    TRELLO_KEY=...  TRELLO_TOKEN=...  python3 scripts/setup_trello.py

Creates (idempotently):
  * Board "SmartBank"
  * Lists: Backlog / To Do / In Progress / In Review / Done
  * Labels: Critical / High / Medium / Low / FR / NFR / Use Case / Risk
  * Cards for every FR-xx, NFR-xx, UC-xx, Rx from the requirements spec,
    with descriptions, priorities, and acceptance criteria.

If a board with this name already exists it is reused and cards are
appended only when missing (so re-running is safe).
"""
import os
import sys
import time
import requests

API = "https://api.trello.com/1"
KEY = os.environ.get("TRELLO_KEY")
TOKEN = os.environ.get("TRELLO_TOKEN")
if not KEY or not TOKEN:
    sys.exit("Set TRELLO_KEY and TRELLO_TOKEN env vars")

AUTH = {"key": KEY, "token": TOKEN}


def get(path, **params):
    r = requests.get(f"{API}{path}", params={**AUTH, **params})
    r.raise_for_status()
    return r.json()


def post(path, **data):
    r = requests.post(f"{API}{path}", params=AUTH, data=data)
    r.raise_for_status()
    return r.json()


# ---------- board ----------

def ensure_board(name="SmartBank"):
    for b in get("/members/me/boards", fields="name"):
        if b["name"] == name:
            print(f"reusing board {name} ({b['id']})")
            return b["id"]
    print(f"creating board {name}")
    b = post("/boards", name=name,
             desc="SmartBank — Bank Account Management System (Software "
                  "Engineering coursework). Scrum backlog generated from "
                  "Quest2&3 requirements spec.",
             defaultLists="false")
    return b["id"]


def ensure_lists(board_id, names):
    existing = {l["name"]: l["id"] for l in get(f"/boards/{board_id}/lists")}
    result = {}
    for i, name in enumerate(names):
        if name in existing:
            result[name] = existing[name]
        else:
            print(f"  + list {name}")
            lst = post("/lists", name=name, idBoard=board_id, pos=(i + 1) * 1000)
            result[name] = lst["id"]
    return result


def ensure_labels(board_id, spec):
    """spec = {name: color}"""
    existing = {l["name"]: l["id"] for l in get(f"/boards/{board_id}/labels")
                if l["name"]}
    result = {}
    for name, color in spec.items():
        if name in existing:
            result[name] = existing[name]
        else:
            print(f"  + label {name}")
            lab = post("/labels", name=name, color=color, idBoard=board_id)
            result[name] = lab["id"]
    return result


def ensure_card(list_id, name, desc, label_ids, existing_names):
    if name in existing_names:
        return
    print(f"  + card {name}")
    post("/cards", idList=list_id, name=name, desc=desc,
         idLabels=",".join(label_ids), pos="bottom")
    time.sleep(0.15)  # be gentle with the API


def list_card_names(board_id):
    return {c["name"] for c in get(f"/boards/{board_id}/cards", fields="name")}


# ---------- data ----------

FUNCTIONAL = [
    ("FR-01 User Registration",
     "High",
     "As a new visitor I can create a customer account with username, email, "
     "and password so that I can access the banking application.\n\n"
     "**Acceptance criteria**\n"
     "- Password minimum 6 characters\n"
     "- Email must be unique and well-formed\n"
     "- A default bank account is opened on registration\n"
     "- User receives a confirmation and can log in immediately"),
    ("FR-02 User Authentication",
     "High",
     "As a registered user I can securely log in and log out.\n\n"
     "**Acceptance criteria**\n"
     "- Valid credentials grant access, invalid are rejected\n"
     "- Blocked accounts cannot log in\n"
     "- Session expires / can be cleared via logout"),
    ("FR-03 Account Overview",
     "High",
     "As a logged-in customer I can see all my accounts with balance, "
     "currency, and status on the dashboard.\n\n"
     "**Acceptance criteria**\n"
     "- Dashboard displays account number, balance, status correctly\n"
     "- Works for multiple accounts per user"),
    ("FR-04 Transaction History",
     "Medium",
     "As a customer I can view the history of all transactions for a given "
     "account.\n\n"
     "**Acceptance criteria**\n"
     "- All past operations displayed with date, amount, type\n"
     "- Sorted newest first"),
    ("FR-05 Money Transfer",
     "High",
     "As a customer I can transfer funds between accounts.\n\n"
     "**Acceptance criteria**\n"
     "- Sender balance decreases, recipient balance increases\n"
     "- Insufficient funds blocked\n"
     "- Same-account transfer blocked\n"
     "- Unknown recipient account blocked\n"
     "- Both users receive a notification"),
    ("FR-06 Deposits and Withdrawals",
     "High",
     "As a customer I can deposit funds and withdraw funds from my account.\n\n"
     "**Acceptance criteria**\n"
     "- Deposit increases balance\n"
     "- Withdrawal blocked on insufficient funds\n"
     "- Amount must be positive"),
    ("FR-07 Profile Management",
     "Medium",
     "As a customer I can update selected profile details (name, email, "
     "phone, address).\n\n"
     "**Acceptance criteria**\n"
     "- Changes persist and are visible immediately"),
    ("FR-08 Notifications",
     "Medium",
     "As a customer I receive notifications about completed transactions "
     "and important account events.\n\n"
     "**Acceptance criteria**\n"
     "- Every deposit/withdraw/transfer creates a notification row\n"
     "- User can view all notifications in one place"),
    ("FR-09 Administrative Panel",
     "Medium",
     "As an administrator I have a dashboard for managing users and "
     "accounts.\n\n"
     "**Acceptance criteria**\n"
     "- Admin-only access (403 for customers)\n"
     "- Shows user list and recent transactions"),
    ("FR-10 Account Management by Administrator",
     "Medium",
     "As an administrator I can block or unblock user accounts.\n\n"
     "**Acceptance criteria**\n"
     "- Block status cascades to the user's bank accounts\n"
     "- Action is written to the audit log\n"
     "- Blocked user cannot log in"),
]

NON_FUNCTIONAL = [
    ("NFR-01 Security",
     "Critical",
     "All communication encrypted via HTTPS; passwords stored with a "
     "secure hash (pbkdf2-sha256); parameterized SQL; role-based access "
     "control."),
    ("NFR-02 Performance",
     "High",
     "API response time under 2 seconds for standard operations; system "
     "supports at least 100 concurrent users."),
    ("NFR-03 Reliability",
     "High",
     "System uptime 99.5%, automated daily database backups, graceful "
     "error handling with transactional rollback."),
    ("NFR-04 Usability",
     "Medium",
     "New users can complete core tasks without external help; interface "
     "meets WCAG 2.1 AA accessibility standards."),
    ("NFR-05 Scalability",
     "Medium",
     "New modules can be added without modifying existing core "
     "functionality."),
    ("NFR-06 Compatibility",
     "Medium",
     "Application functions correctly on Chrome, Firefox, Safari, and "
     "Edge; responsive layout for mobile devices."),
]

USE_CASES = [
    ("UC-01 User Registration",
     "High",
     "Actor: Customer. Precondition: no account yet.\n\n"
     "Main scenario:\n"
     "1. Open registration page\n"
     "2. Enter personal data\n"
     "3. System validates input\n"
     "4. System creates user account\n"
     "5. System sends confirmation\n"
     "6. User redirected to login\n\n"
     "Alternative:\n"
     "- 3a. Email already registered → error\n"
     "- 3b. Password policy violated → error"),
    ("UC-02 Money Transfer",
     "High",
     "Actor: Customer. Precondition: logged in, sufficient funds.\n\n"
     "Main scenario:\n"
     "1. Navigate to transfer page\n"
     "2. Enter recipient account, amount, description\n"
     "3. System validates recipient and balance\n"
     "4. System requests OTP\n"
     "5. User enters OTP\n"
     "6. System debits sender and credits recipient\n"
     "7. System creates transaction record and notifies user\n\n"
     "Alternative:\n"
     "- 3a. Insufficient funds → error\n"
     "- 5a. Invalid OTP up to 3 retries, then block"),
    ("UC-03 Account Management by Administrator",
     "Medium",
     "Actor: Administrator. Precondition: logged in with admin role.\n\n"
     "Main scenario:\n"
     "1. Open admin dashboard\n"
     "2. Search user by name/email/account number\n"
     "3. System displays details and recent transactions\n"
     "4. Admin reviews, blocks or deactivates\n"
     "5. System applies change and logs action"),
]

RISKS = [
    ("R1 Integration complexity",
     "High",
     "Probability: Medium. Impact: High. Mitigation: REST API contracts, "
     "regular integration testing, Docker dev environments."),
    ("R2 Security vulnerabilities",
     "Critical",
     "Probability: Medium. Impact: Critical. Mitigation: OWASP guidelines, "
     "parameterized queries, HTTPS, input validation, pre-deployment audit."),
    ("R3 Technology learning curve",
     "Medium",
     "Probability: Low. Impact: Medium. Mitigation: learning sprint, pair "
     "programming, code reviews."),
    ("R4 Schedule delays",
     "High",
     "Probability: Medium. Impact: High. Mitigation: buffer time, weekly "
     "progress meetings, task redistribution."),
    ("R5 Communication gaps",
     "Medium",
     "Probability: Low. Impact: Medium. Mitigation: shared project tool, "
     "stand-ups, living documentation."),
    ("R6 Changing requirements",
     "Medium",
     "Probability: Low. Impact: Medium. Mitigation: Agile/Scrum, flexible "
     "architecture, change log."),
    ("R7 Data loss",
     "Critical",
     "Probability: Low. Impact: Critical. Mitigation: Git + GitHub, regular "
     "backups, cloud documentation storage."),
]


# ---------- main ----------

def main():
    board_id = ensure_board()
    print("lists:")
    lists = ensure_lists(board_id,
                         ["Backlog", "To Do", "In Progress", "In Review", "Done"])

    print("labels:")
    labels = ensure_labels(board_id, {
        "Critical": "red",
        "High": "orange",
        "Medium": "yellow",
        "Low": "sky",
        "FR": "blue",
        "NFR": "purple",
        "Use Case": "green",
        "Risk": "pink",
    })

    existing = list_card_names(board_id)
    backlog = lists["Backlog"]

    print("cards:")
    for name, prio, desc in FUNCTIONAL:
        ensure_card(backlog, name, desc,
                    [labels[prio], labels["FR"]], existing)

    for name, prio, desc in NON_FUNCTIONAL:
        ensure_card(backlog, name, desc,
                    [labels[prio], labels["NFR"]], existing)

    for name, prio, desc in USE_CASES:
        ensure_card(backlog, name, desc,
                    [labels[prio], labels["Use Case"]], existing)

    for name, prio, desc in RISKS:
        ensure_card(backlog, name, desc,
                    [labels[prio], labels["Risk"]], existing)

    print(f"\ndone. board id: {board_id}")
    print(f"url: https://trello.com/b/{board_id}")


if __name__ == "__main__":
    main()
