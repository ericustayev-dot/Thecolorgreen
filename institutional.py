"""Tracks what well-known hedge funds are buying/selling, based on their
quarterly SEC Form 13F filings - the only legally required disclosure of
institutional holdings. This data is inherently delayed: funds have up to
45 days after each calendar quarter ends to file, so this always shows
recently-disclosed positions from the last reported quarter, never live
trading activity. A "buy" here means a new or increased position between
two consecutive quarterly filings, not a trade made today."""

import json
import os
import time
import urllib.request
import xml.etree.ElementTree as ET
from datetime import date

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
INSTITUTIONAL_FILE = os.path.join(BASE_DIR, "institutional_activity.json")

USER_AGENT = "TheColorGreen personal-project ericustayev@gmail.com"
REQUEST_DELAY = 0.15  # stay well under SEC's 10 req/sec fair-access limit

# Well-known "guru" investors with concentrated, actively-managed portfolios -
# chosen over giant index managers (BlackRock, Vanguard) whose 13Fs just
# mirror broad indexes and aren't really "picks" in the same interesting sense.
FUNDS = {
    "Bridgewater Associates (Ray Dalio)": "0001350694",
    "Berkshire Hathaway (Warren Buffett)": "0001067983",
    "Pershing Square (Bill Ackman)": "0001336528",
    "Scion Asset Management (Michael Burry)": "0001649339",
    "Third Point (Dan Loeb)": "0001040273",
    "Appaloosa Management (David Tepper)": "0001656456",
    "Duquesne Family Office (Stanley Druckenmiller)": "0001536411",
    "Renaissance Technologies": "0001037389",
    "Citadel Advisors (Ken Griffin)": "0001423053",
    "Soros Fund Management": "0001029160",
}


def _fetch_json(url: str) -> dict:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = json.loads(resp.read())
    time.sleep(REQUEST_DELAY)
    return data


def _fetch_text(url: str) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=30) as resp:
        text = resp.read().decode("utf-8", errors="replace")
    time.sleep(REQUEST_DELAY)
    return text


def _strip_ns(tag: str) -> str:
    return tag.split("}")[-1] if "}" in tag else tag


def get_recent_13f_filings(cik: str, count: int = 2) -> list[dict]:
    """Returns up to `count` most recent 13F-HR filings (accession + date)."""
    data = _fetch_json(f"https://data.sec.gov/submissions/CIK{cik}.json")
    recent = data["filings"]["recent"]
    filings = []
    for form, filing_date, accession in zip(recent["form"], recent["filingDate"], recent["accessionNumber"]):
        if form == "13F-HR":
            filings.append({"date": filing_date, "accession": accession})
            if len(filings) >= count:
                break
    return filings


def get_infotable_holdings(cik: str, accession: str) -> list[dict]:
    """Downloads and parses the holdings table for one 13F filing.
    Some filing agents name this file descriptively ("infotable.xml"),
    others use a plain numeric name ("53405.xml") - so instead of guessing
    from the filename, every candidate XML file is fetched and checked by
    its actual root tag until the real information table is found."""
    cik_num = str(int(cik))
    acc_nodash = accession.replace("-", "")
    base_url = f"https://www.sec.gov/Archives/edgar/data/{cik_num}/{acc_nodash}"
    index = _fetch_json(f"{base_url}/index.json")

    candidates = [
        item["name"] for item in index["directory"]["item"]
        if item["name"].endswith(".xml") and item["name"] != "primary_doc.xml"
    ]

    root = None
    for filename in candidates:
        xml_text = _fetch_text(f"{base_url}/{filename}")
        try:
            candidate_root = ET.fromstring(xml_text)
        except ET.ParseError:
            continue
        if _strip_ns(candidate_root.tag) == "informationTable":
            root = candidate_root
            break
    if root is None:
        return []

    # Large filers often split one security across multiple line items in
    # the same filing (different sub-accounts/voting authority types), so
    # entries are aggregated by CUSIP into a single total position.
    by_cusip = {}
    for info_table in root:
        if _strip_ns(info_table.tag) != "infoTable":
            continue
        fields = {_strip_ns(child.tag): child for child in info_table}
        name_el = fields.get("nameOfIssuer")
        cusip_el = fields.get("cusip")
        value_el = fields.get("value")
        shares_el = fields.get("shrsOrPrnAmt")
        shares = 0
        if shares_el is not None:
            for sub in shares_el:
                if _strip_ns(sub.tag) == "sshPrnamt":
                    shares = int(sub.text)
        if name_el is None or cusip_el is None:
            continue

        cusip = cusip_el.text
        value = int(value_el.text) if value_el is not None else 0
        if cusip in by_cusip:
            by_cusip[cusip]["shares"] += shares
            by_cusip[cusip]["value_usd"] += value
        else:
            by_cusip[cusip] = {"name": name_el.text, "cusip": cusip, "value_usd": value, "shares": shares}

    return list(by_cusip.values())


def diff_holdings(current: list[dict], previous: list[dict]) -> list[dict]:
    """Compares two quarters of holdings by CUSIP and classifies each move.
    Unchanged positions are omitted - only actual portfolio changes count as
    'activity'."""
    prev_by_cusip = {h["cusip"]: h for h in previous}
    curr_by_cusip = {h["cusip"]: h for h in current}

    moves = []
    for cusip, curr in curr_by_cusip.items():
        prev = prev_by_cusip.get(cusip)
        if prev is None:
            moves.append({**curr, "action": "new", "change_pct": None})
        elif curr["shares"] > prev["shares"]:
            pct = round((curr["shares"] - prev["shares"]) / prev["shares"] * 100, 1) if prev["shares"] else None
            moves.append({**curr, "action": "increased", "change_pct": pct})
        elif curr["shares"] < prev["shares"]:
            pct = round((curr["shares"] - prev["shares"]) / prev["shares"] * 100, 1) if prev["shares"] else None
            moves.append({**curr, "action": "reduced", "change_pct": pct})

    for cusip, prev in prev_by_cusip.items():
        if cusip not in curr_by_cusip:
            moves.append({**prev, "action": "sold_out", "shares": 0, "change_pct": -100.0})

    return moves


def compute_fund_activity(fund_name: str, cik: str) -> dict:
    filings = get_recent_13f_filings(cik, count=2)
    if not filings:
        return {"fund": fund_name, "cik": cik, "filing_date": None, "buys": [], "sells": []}

    current_holdings = get_infotable_holdings(cik, filings[0]["accession"])
    previous_holdings = get_infotable_holdings(cik, filings[1]["accession"]) if len(filings) > 1 else []

    moves = diff_holdings(current_holdings, previous_holdings)

    # Cap buys and sells separately - otherwise a fund that opened many new
    # positions this quarter could crowd sells out of a single shared cap.
    buy_order = {"new": 0, "increased": 1}
    sell_order = {"reduced": 0, "sold_out": 1}
    buys = sorted((m for m in moves if m["action"] in buy_order),
                  key=lambda m: (buy_order[m["action"]], -m.get("value_usd", 0)))[:15]
    sells = sorted((m for m in moves if m["action"] in sell_order),
                   key=lambda m: (sell_order[m["action"]], -m.get("value_usd", 0)))[:15]

    return {
        "fund": fund_name,
        "cik": cik,
        "filing_date": filings[0]["date"],
        "previous_filing_date": filings[1]["date"] if len(filings) > 1 else None,
        "buys": buys,
        "sells": sells,
    }


def load_previous() -> dict:
    if not os.path.exists(INSTITUTIONAL_FILE):
        return {}
    with open(INSTITUTIONAL_FILE) as f:
        return json.load(f)


def save(data: dict) -> None:
    with open(INSTITUTIONAL_FILE, "w") as f:
        json.dump(data, f, indent=2)


def compute_all_institutional_activity(force: bool = False) -> dict:
    previous = load_previous()
    today = date.today().isoformat()
    if not force and previous.get("computed_date") == today:
        return previous

    funds = []
    for fund_name, cik in FUNDS.items():
        try:
            funds.append(compute_fund_activity(fund_name, cik))
        except Exception as e:
            funds.append({"fund": fund_name, "cik": cik, "filing_date": None, "buys": [], "sells": [], "error": str(e)})

    result = {"computed_date": today, "funds": funds}
    save(result)
    return result


if __name__ == "__main__":
    result = compute_all_institutional_activity(force=True)
    for f in result["funds"]:
        if f.get("error"):
            print(f"\n=== {f['fund']}: ERROR - {f['error']} ===")
            continue
        print(f"\n=== {f['fund']} (filed {f['filing_date']}, vs {f['previous_filing_date']}) ===")
        print(f"  Buys ({len(f['buys'])}):")
        for m in f["buys"][:5]:
            pct = f" ({m['change_pct']:+.1f}%)" if m.get("change_pct") is not None else ""
            print(f"    {m['action']:10} {m['name']:30} ${m['value_usd']:>15,}{pct}")
        print(f"  Sells ({len(f['sells'])}):")
        for m in f["sells"][:5]:
            pct = f" ({m['change_pct']:+.1f}%)" if m.get("change_pct") is not None else ""
            print(f"    {m['action']:10} {m['name']:30} ${m['value_usd']:>15,}{pct}")
