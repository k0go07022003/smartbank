"""Assign Trello cards to team members based on their role.

Team split taken from Quest2&3.docx:

* **Daniel Bober** — Project Manager + Backend Developer.
  Owns backend logic, authentication, money movement, admin API,
  security hardening, sprint planning.
* **k0go (Szymon Adamek)** — DBA + QA + Frontend.
  Owns database schema, test suite, UI/UX, DevOps (Docker, CI,
  backups, deployment), documentation.

This script walks every card on the SmartBank board and assigns one
or both members based on the mapping below. Idempotent — re-running
does not duplicate assignments.
"""
import os
import sys
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed

API = "https://api.trello.com/1"
AUTH = {"key": os.environ["TRELLO_KEY"], "token": os.environ["TRELLO_TOKEN"]}

DANIEL = "5eccb48a21dfdf2fd5407cd6"  # danielbober3
SZYMON = "5e88d8da8028e813a96cf9ab"  # hitech65 / k0go
BOTH = [DANIEL, SZYMON]


# ---------- assignment matrix ----------
#
# Each card title maps to a list of member IDs. Cards where both
# members collaborate (e.g. full-stack features) get both IDs.

ASSIGNMENTS = {
    # ============= FUNCTIONAL REQUIREMENTS =============
    # Pure backend (Daniel) vs full-stack (both)
    "FR-01 User Registration":                    BOTH,    # backend + form
    "FR-02 User Authentication":                  [DANIEL],
    "FR-03 Account Overview":                     [SZYMON],  # dashboard UI
    "FR-04 Transaction History":                  [SZYMON],  # table UI
    "FR-05 Money Transfer":                       [DANIEL],
    "FR-06 Deposits and Withdrawals":             [DANIEL],
    "FR-07 Profile Management":                   [SZYMON],  # form UX
    "FR-08 Notifications":                        BOTH,
    "FR-09 Administrative Panel":                 BOTH,
    "FR-10 Account Management by Administrator":  [DANIEL],

    # ============= NON-FUNCTIONAL =============
    "NFR-01 Security":          [DANIEL],   # hashing + RBAC
    "NFR-02 Performance":       [DANIEL],
    "NFR-03 Reliability":       [DANIEL],
    "NFR-04 Usability":         [SZYMON],   # frontend/UX
    "NFR-05 Scalability":       BOTH,       # architecture
    "NFR-06 Compatibility":     [SZYMON],   # frontend/cross-browser

    # ============= USE CASES =============
    "UC-01 User Registration":                      BOTH,
    "UC-02 Money Transfer":                         [DANIEL],
    "UC-03 Account Management by Administrator":    [DANIEL],

    # ============= RISKS =============
    "R1 Integration complexity":      [DANIEL],   # PM
    "R2 Security vulnerabilities":    [DANIEL],   # backend
    "R3 Technology learning curve":   BOTH,
    "R4 Schedule delays":             [DANIEL],   # PM
    "R5 Communication gaps":          BOTH,
    "R6 Changing requirements":       [DANIEL],   # PM
    "R7 Data loss":                   [SZYMON],   # DBA

    # ============= SPRINT 1 — FOUNDATION =============
    "Project scaffold & git init":           [SZYMON],
    "Domain layer: models.py":               [DANIEL],
    "HTTP layer: routes.py + blueprints":    [DANIEL],
    "Jinja2 templates + base layout":        [SZYMON],
    "Modern fintech UI (CSS)":               [SZYMON],

    # ============= SPRINT 2 — TESTING =============
    "Pytest fixtures + test infrastructure":  [SZYMON],
    "Unit tests for domain logic":            [SZYMON],
    "Integration tests for HTTP layer":       [SZYMON],

    # ============= SPRINT 3 — DOCS =============
    "README with setup and traceability":     [SZYMON],
    "DESIGN_PATTERNS catalog (MD + PDF)":     BOTH,
    "pdoc HTML API docs generated":           [SZYMON],

    # ============= SPRINT 4 — SCRUM =============
    "Trello board provisioning":              [SZYMON],

    # ============= SPRINT 5 — HARDENING =============
    "Load test with 100 concurrent users":    [SZYMON],  # QA
    "OWASP security audit checklist":         [DANIEL],
    "OTP verification for money transfers":   [DANIEL],
    "Email notifications via SMTP":           [DANIEL],
    "Admin dashboard charts":                 [SZYMON],
    "Docker containerization":                [SZYMON],  # DevOps
    "GitHub Actions CI pipeline":             [SZYMON],
    "Automated daily SQLite backup":          [SZYMON],  # DBA
    "Structured logging with request IDs":    [DANIEL],
    "WCAG 2.1 AA accessibility audit":        [SZYMON],  # frontend
    "Database migration tool (alembic)":      [SZYMON],  # DBA
    "User manual (PL + EN)":                  [SZYMON],
    "User acceptance testing (UAT) session":  BOTH,
    "Final deployment to staging":            BOTH,

    # ============= BUGS / CHORES =============
    "BUG: scrypt unavailable on macOS Python 3.9":  [SZYMON],
    "CHORE: upgrade Python to 3.12 in dev":         [SZYMON],

    # ============= SCRUM CEREMONIES =============
    "Sprint planning — Sprint 5 kickoff":     [DANIEL],  # PM
    "Daily standups — async via Discord":     BOTH,
    "Sprint retro after Sprint 4":            BOTH,
}

NAMES = {DANIEL: "Daniel", SZYMON: "Szymon"}


# ---------- operations ----------

def req(method, path, **params):
    r = requests.request(method, f"{API}{path}", params={**AUTH, **params})
    r.raise_for_status()
    return r.json() if r.content else {}


def get(p, **k): return req("GET", p, **k)
def post(p, **k): return req("POST", p, **k)
def delete(p, **k): return req("DELETE", p, **k)


def find_board(name="SmartBank"):
    for b in get("/members/me/boards", fields="name"):
        if b["name"] == name:
            return b["id"]
    sys.exit("board not found")


def assign_one(card, wanted):
    """Ensure ``card`` is assigned exactly to ``wanted`` members."""
    current = set(card.get("idMembers", []))
    desired = set(wanted)

    added = desired - current
    removed = current - desired

    for mid in added:
        post(f"/cards/{card['id']}/idMembers", value=mid)
    for mid in removed:
        delete(f"/cards/{card['id']}/idMembers/{mid}")

    if not added and not removed:
        return f"- unchanged  {card['name']}"
    names = ", ".join(NAMES[m] for m in desired)
    return f"✓ {card['name']}  ->  {names}"


def main():
    board_id = find_board()
    cards = get(f"/boards/{board_id}/cards", fields="name,idMembers")
    by_name = {c["name"]: c for c in cards}

    print(f"{len(cards)} cards on board, {len(ASSIGNMENTS)} in matrix\n")

    # Sanity: warn about any card without an assignment entry
    missing = [c["name"] for c in cards if c["name"] not in ASSIGNMENTS]
    if missing:
        print("WARNING — cards without an entry in ASSIGNMENTS:")
        for m in missing:
            print(f"  ? {m}")
        print()

    tasks = []
    for title, members in ASSIGNMENTS.items():
        card = by_name.get(title)
        if card is None:
            tasks.append(lambda t=title: f"?? card not found: {t}")
            continue
        tasks.append(lambda c=card, m=members: assign_one(c, m))

    with ThreadPoolExecutor(max_workers=6) as ex:
        for f in as_completed([ex.submit(t) for t in tasks]):
            print(f"  {f.result()}")

    # Summary
    print()
    daniel_cnt = sum(1 for v in ASSIGNMENTS.values() if DANIEL in v)
    szymon_cnt = sum(1 for v in ASSIGNMENTS.values() if SZYMON in v)
    shared = sum(1 for v in ASSIGNMENTS.values() if DANIEL in v and SZYMON in v)
    print(f"Daniel  : {daniel_cnt} cards ({shared} shared)")
    print(f"Szymon  : {szymon_cnt} cards ({shared} shared)")


if __name__ == "__main__":
    main()
