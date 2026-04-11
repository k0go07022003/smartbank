"""Reflect current implementation progress onto the Trello board.

Moves cards for already-implemented items into "Done" and updates a
few long-running risks/NFRs into the right columns, so the board
matches reality after running ``setup_trello.py``.
"""
import os
import sys
import requests

API = "https://api.trello.com/1"
KEY = os.environ["TRELLO_KEY"]
TOKEN = os.environ["TRELLO_TOKEN"]
AUTH = {"key": KEY, "token": TOKEN}


def get(path, **params):
    r = requests.get(f"{API}{path}", params={**AUTH, **params})
    r.raise_for_status()
    return r.json()


def put(path, **data):
    r = requests.put(f"{API}{path}", params=AUTH, data=data)
    r.raise_for_status()
    return r.json()


def find_board(name="SmartBank"):
    for b in get("/members/me/boards", fields="name"):
        if b["name"] == name:
            return b["id"]
    sys.exit(f"board {name} not found — run setup_trello.py first")


def move(cards_by_name, list_id, names):
    for name in names:
        card = cards_by_name.get(name)
        if card is None:
            print(f"  ?? card not found: {name}")
            continue
        put(f"/cards/{card['id']}", idList=list_id)
        print(f"  -> {name}")


def main():
    board_id = find_board()
    lists = {l["name"]: l["id"] for l in get(f"/boards/{board_id}/lists")}
    cards = {c["name"]: c for c in get(f"/boards/{board_id}/cards")}

    done_now = [
        # All 10 functional requirements are implemented and tested
        "FR-01 User Registration",
        "FR-02 User Authentication",
        "FR-03 Account Overview",
        "FR-04 Transaction History",
        "FR-05 Money Transfer",
        "FR-06 Deposits and Withdrawals",
        "FR-07 Profile Management",
        "FR-08 Notifications",
        "FR-09 Administrative Panel",
        "FR-10 Account Management by Administrator",
        # Non-functional items we already satisfy
        "NFR-01 Security",
        "NFR-04 Usability",
        "NFR-06 Compatibility",
        # All three written use cases are implemented
        "UC-01 User Registration",
        "UC-02 Money Transfer",
        "UC-03 Account Management by Administrator",
    ]

    in_review = [
        # Non-functional items that are in place but worth one more pass
        "NFR-02 Performance",
        "NFR-03 Reliability",
        "NFR-05 Scalability",
    ]

    print(f"-> Done ({len(done_now)} cards):")
    move(cards, lists["Done"], done_now)

    print(f"-> In Review ({len(in_review)} cards):")
    move(cards, lists["In Review"], in_review)

    print("\nrisks stay in Backlog — they are ongoing concerns, not work items.")


if __name__ == "__main__":
    main()
