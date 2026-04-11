"""Remove leading emoji characters from every Trello card name on the
SmartBank board. Idempotent — running twice is a no-op.
"""
import os
import re
import sys
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed

API = "https://api.trello.com/1"
AUTH = {"key": os.environ["TRELLO_KEY"], "token": os.environ["TRELLO_TOKEN"]}

# Covers emoji blocks, variation selectors, ZWJ, skin tones
EMOJI_RE = re.compile(
    r"[\U0001F1E6-\U0001F1FF"  # regional indicators
    r"\U0001F300-\U0001F5FF"   # symbols & pictographs
    r"\U0001F600-\U0001F64F"   # emoticons
    r"\U0001F680-\U0001F6FF"   # transport & map
    r"\U0001F700-\U0001F77F"
    r"\U0001F780-\U0001F7FF"
    r"\U0001F800-\U0001F8FF"
    r"\U0001F900-\U0001F9FF"   # supplemental symbols & pictographs
    r"\U0001FA00-\U0001FA6F"
    r"\U0001FA70-\U0001FAFF"
    r"\U00002300-\U000023FF"   # misc technical (⏰, ⌛, ⏳, ...)
    r"\U00002600-\U000027BF"   # misc symbols + dingbats
    r"\U0000FE0F"              # variation selector-16
    r"\U0000200D"              # ZWJ
    r"]+",
    flags=re.UNICODE,
)


def strip_emoji(s):
    # remove emoji, then collapse whitespace
    return re.sub(r"\s+", " ", EMOJI_RE.sub("", s)).strip()


def req(method, path, **params):
    r = requests.request(method, f"{API}{path}", params={**AUTH, **params})
    r.raise_for_status()
    return r.json() if r.content else {}


def get(p, **k): return req("GET", p, **k)
def put(p, **k): return req("PUT", p, **k)


def find_board(name="SmartBank"):
    for b in get("/members/me/boards", fields="name"):
        if b["name"] == name:
            return b["id"]
    sys.exit("board not found")


def fix_card(card):
    new = strip_emoji(card["name"])
    if new == card["name"]:
        return f"- unchanged: {new}"
    put(f"/cards/{card['id']}", name=new)
    return f"✓ {card['name']}  ->  {new}"


def main():
    board_id = find_board()
    cards = get(f"/boards/{board_id}/cards", fields="name")
    print(f"processing {len(cards)} cards")

    with ThreadPoolExecutor(max_workers=6) as ex:
        for f in as_completed([ex.submit(fix_card, c) for c in cards]):
            print(f"  {f.result()}")

    print("done.")


if __name__ == "__main__":
    main()
