"""TenderHawk: watch the Almadar procurement portal and warn sales when rival
Brightline Contracting is likely to bid on a tender we want."""
import json
import re
import sys
import urllib.request

PORTAL_URL = "https://portal.almadar.example/tenders.json"
RIVAL = "Brightline Contracting"
OUR_SECTORS = ["roadworks", "drainage", "street lighting"]
RIVAL_HISTORY_FILE = "brightline_past_bids.json"


def fetch_tenders():
    with urllib.request.urlopen(PORTAL_URL) as r:
        return json.loads(r.read())


def clean(tender):
    title = re.sub(r"\s+", " ", tender.get("title", "")).strip().lower()
    value = float(str(tender.get("value", "0")).replace(",", "") or 0)
    return {"id": tender["id"], "title": title, "value": value, "region": tender.get("region", "").lower()}


def is_ours(tender):
    return any(s in tender["title"] for s in OUR_SECTORS)


def rival_likelihood(tender, history):
    same_region = [h for h in history if h["region"] == tender["region"]]
    if not same_region:
        return 0.0
    similar = [h for h in same_region if abs(h["value"] - tender["value"]) <= 0.25 * tender["value"]]
    return round(len(similar) / len(same_region), 2)


def main():
    history = json.load(open(RIVAL_HISTORY_FILE))
    for raw in fetch_tenders():
        t = clean(raw)
        if not is_ours(t):
            continue
        p = rival_likelihood(t, history)
        if p >= 0.5:
            print(f"WARNING {RIVAL} likely to bid on {t['id']} ({t['title']}): {p}")


if __name__ == "__main__":
    sys.exit(main())
