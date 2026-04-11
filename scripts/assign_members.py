"""Assign Trello cards to team members based on their role.

Team split taken from Quest2&3.docx:

* **Daniel Bober** — Project Manager + Backend Developer.
  Owns backend logic, authentication, money movement, admin API,
  security hardening, sprint planning.
* **Kamil Bialik** — Frontend Developer + UX Designer.
  Owns the user interface, templates, CSS, wireframes, usability
  testing, and cross-browser/accessibility work.
* **Szymon Adamek (k0go)** — DBA + QA Tester.
  Owns database schema, pytest suite, DevOps (Docker, CI, backups,
  deployment), written project documentation.

This script walks every card on the SmartBank board and assigns one
or more members based on the mapping below. Idempotent — re-running
does not duplicate assignments.
"""
import os
import sys
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed

API = "https://api.trello.com/1"
AUTH = {"key": os.environ["TRELLO_KEY"], "token": os.environ["TRELLO_TOKEN"]}

DANIEL = "5eccb48a21dfdf2fd5407cd6"  # danielbober3
KAMIL  = "69da513acc9c3bc753de9b66"  # kamilbialik
SZYMON = "5e88d8da8028e813a96cf9ab"  # hitech65 / k0go
ALL = [DANIEL, KAMIL, SZYMON]


# ---------- assignment matrix ----------
#
# Each card title maps to a list of member IDs. Cards where both
# members collaborate (e.g. full-stack features) get both IDs.

ASSIGNMENTS = {
    # ============= FUNCTIONAL REQUIREMENTS =============
    "FR-01 User Registration":                    [DANIEL, KAMIL],  # backend + form UX
    "FR-02 User Authentication":                  [DANIEL, KAMIL],  # backend + login form
    "FR-03 Account Overview":                     [KAMIL],          # dashboard UI
    "FR-04 Transaction History":                  [KAMIL],          # table UI
    "FR-05 Money Transfer":                       [DANIEL, KAMIL],  # backend + transfer form
    "FR-06 Deposits and Withdrawals":             [DANIEL],
    "FR-07 Profile Management":                   [KAMIL],          # form UX
    "FR-08 Notifications":                        [DANIEL, KAMIL],  # pub-sub + UI list
    "FR-09 Administrative Panel":                 [DANIEL, KAMIL],  # API + admin UI
    "FR-10 Account Management by Administrator":  [DANIEL],

    # ============= NON-FUNCTIONAL =============
    "NFR-01 Security":          [DANIEL],          # hashing + RBAC
    "NFR-02 Performance":       [DANIEL, SZYMON],  # backend + load testing
    "NFR-03 Reliability":       [DANIEL, SZYMON],  # rollback + backups
    "NFR-04 Usability":         [KAMIL],           # UX domain
    "NFR-05 Scalability":       [DANIEL, SZYMON],  # backend architecture + DB
    "NFR-06 Compatibility":     [KAMIL],           # cross-browser, responsive

    # ============= USE CASES =============
    "UC-01 User Registration":                      [DANIEL, KAMIL],
    "UC-02 Money Transfer":                         [DANIEL, KAMIL],
    "UC-03 Account Management by Administrator":    [DANIEL, KAMIL],

    # ============= RISKS =============
    "R1 Integration complexity":      [DANIEL],          # PM
    "R2 Security vulnerabilities":    [DANIEL],          # backend
    "R3 Technology learning curve":   ALL,
    "R4 Schedule delays":             [DANIEL],          # PM
    "R5 Communication gaps":          ALL,
    "R6 Changing requirements":       [DANIEL],          # PM
    "R7 Data loss":                   [SZYMON],          # DBA

    # ============= SPRINT 1 — FOUNDATION =============
    "Project scaffold & git init":           [SZYMON],
    "Domain layer: models.py":               [DANIEL],
    "HTTP layer: routes.py + blueprints":    [DANIEL],
    "Jinja2 templates + base layout":        [KAMIL],
    "Modern fintech UI (CSS)":               [KAMIL],

    # ============= SPRINT 2 — TESTING =============
    "Pytest fixtures + test infrastructure":  [SZYMON],
    "Unit tests for domain logic":            [SZYMON],
    "Integration tests for HTTP layer":       [SZYMON],

    # ============= SPRINT 3 — DOCS =============
    "README with setup and traceability":     [SZYMON],
    "DESIGN_PATTERNS catalog (MD + PDF)":     [DANIEL, SZYMON],
    "pdoc HTML API docs generated":           [SZYMON],

    # ============= SPRINT 4 — SCRUM =============
    "Trello board provisioning":              [SZYMON],

    # ============= SPRINT 5 — HARDENING =============
    "Load test with 100 concurrent users":    [SZYMON],          # QA
    "OWASP security audit checklist":         [DANIEL],
    "OTP verification for money transfers":   [DANIEL, KAMIL],   # backend + UI
    "Email notifications via SMTP":           [DANIEL],
    "Admin dashboard charts":                 [KAMIL],           # UI/charts
    "Docker containerization":                [SZYMON],          # DevOps
    "GitHub Actions CI pipeline":             [SZYMON],
    "Automated daily SQLite backup":          [SZYMON],          # DBA
    "Structured logging with request IDs":    [DANIEL],
    "WCAG 2.1 AA accessibility audit":        [KAMIL],           # UX domain
    "Database migration tool (alembic)":      [SZYMON],          # DBA
    "User manual (PL + EN)":                  [SZYMON, KAMIL],   # docs + screenshots
    "User acceptance testing (UAT) session":  [KAMIL, SZYMON],   # UX runs, QA records
    "Final deployment to staging":            ALL,

    # ============= BUGS / CHORES =============
    "BUG: scrypt unavailable on macOS Python 3.9":  [SZYMON],
    "CHORE: upgrade Python to 3.12 in dev":         [SZYMON],

    # ============= SCRUM CEREMONIES =============
    "Sprint planning — Sprint 5 kickoff":     [DANIEL],          # PM
    "Daily standups — async via Discord":     ALL,
    "Sprint retro after Sprint 4":            ALL,
}

NAMES = {DANIEL: "Daniel", KAMIL: "Kamil", SZYMON: "Szymon"}


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
    kamil_cnt  = sum(1 for v in ASSIGNMENTS.values() if KAMIL  in v)
    szymon_cnt = sum(1 for v in ASSIGNMENTS.values() if SZYMON in v)
    print(f"Daniel  : {daniel_cnt} cards")
    print(f"Kamil   : {kamil_cnt} cards")
    print(f"Szymon  : {szymon_cnt} cards")


if __name__ == "__main__":
    main()
