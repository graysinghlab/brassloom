
"""
BrassLoom Harvester
Fetches live opportunities from public sources and writes opportunities.json

Sources:
- Grants.gov Search2 API (no API key required)  [docs: https://grants.gov/api/common/search2]
- NIH Guide RSS (FOAs)                           [rss: see https://grants.nih.gov/news-events/subscribe-follow/email-updates-and-rss-feeds]
- NSF funding RSS                                [rss: https://www.nsf.gov/rss]
- NASA MUREP pages / NSPIRES listings            [landing: https://www.nasa.gov/learning-resources/minority-university-research-education-project/murep-opportunities-and-resources/]

Run:
  python brassloom_harvest.py --out opportunities.json --days 60 --keywords "HBCU,MSI,minority serving,tribal,HSI,TCU,Black,underrepresented,broadening participation"

Note:
- Requires: requests, feedparser
- Internet access must be available from your machine.
"""
import argparse, datetime, json, re, sys
from typing import List, Dict
import requests
import feedparser

DEFAULT_KEYWORDS = ["HBCU","MSI","minority serving","Hispanic-Serving","HSI","Tribal","TCU","Alaska Native","Native Hawaiian","Black","broadening participation","EPSCoR"]

def within_days(date_str: str, days: int) -> bool:
    if not date_str:
        return True
    try:
        dt = datetime.datetime.fromisoformat(date_str[:10])
    except ValueError:
        return True
    return (datetime.datetime.utcnow() - dt).days <= days

def score_item(item: Dict, keywords: List[str]) -> int:
    text = " ".join([str(item.get(k,"")) for k in ["title","description","eligibility","agency","source"]]).lower()
    score = 0
    for kw in keywords:
        if kw.lower() in text:
            score += 10
    # Boost for HBCU/MSI exact
    if re.search(r'\bHBCU\b', text, re.I): score += 20
    if re.search(r'\bMSI\b', text, re.I): score += 15
    # Time urgency boost
    if item.get("close_date"):
        try:
            cdt = datetime.datetime.fromisoformat(item["close_date"][:10])
            days_left = (cdt - datetime.datetime.utcnow()).days
            if 0 <= days_left <= 30:
                score += 10
            elif 31 <= days_left <= 60:
                score += 5
        except Exception:
            pass
    return score

def fetch_grants_gov(days: int, keywords: List[str]) -> List[Dict]:
    url = "https://www.grants.gov/api/v2/search/search2"
    # Query last N days and include keyword terms
    query = " OR ".join([f'\"{k}\"' for k in keywords])
    params = {
        "startRecordNum": 0,
        "oppStatuses": "forecasted|posted",
        "sortBy": "openDate|desc",
        "keyword": query
    }
    r = requests.get(url, params=params, timeout=30)
    r.raise_for_status()
    data = r.json()
    out = []
    for opp in data.get("opportunities", []):
        itm = {
            "id": opp.get("opportunityNumber") or opp.get("opportunityId"),
            "source": "Grants.gov",
            "title": opp.get("title"),
            "agency": opp.get("agency"),
            "assistance_listing": opp.get("cfdaList", [{}])[0].get("cfdaNumber",""),
            "posted_date": opp.get("openDate"),
            "close_date": opp.get("closeDate"),
            "eligibility": ", ".join([e.get("eligibilityName","") for e in opp.get("eligibility",[])]),
            "url": opp.get("url"),
            "tags": opp.get("category", []),
            "description": opp.get("synopsis","")[:1500]
        }
        if within_days(itm.get("posted_date",""), days):
            out.append(itm)
    return out

def fetch_rss(feed_url: str, source_name: str) -> List[Dict]:
    d = feedparser.parse(feed_url)
    out = []
    for e in d.entries:
        posted = ""
        if hasattr(e, "published"):
            try:
                posted = datetime.datetime(*e.published_parsed[:6]).date().isoformat()
            except Exception:
                posted = ""
        itm = {
            "id": e.get("id") or e.get("link"),
            "source": source_name,
            "title": e.get("title",""),
            "agency": source_name,
            "assistance_listing": "",
            "posted_date": posted,
            "close_date": "",
            "eligibility": "",
            "url": e.get("link",""),
            "tags": [],
            "description": e.get("summary","")
        }
        out.append(itm)
    return out

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="opportunities.json")
    ap.add_argument("--days", type=int, default=90)
    ap.add_argument("--keywords", default=",".join(DEFAULT_KEYWORDS))
    args = ap.parse_args()
    keywords = [k.strip() for k in args.keywords.split(",") if k.strip()]

    all_items = []

    # Grants.gov
    try:
        all_items += fetch_grants_gov(args.days, keywords)
    except Exception as e:
        print(f"[warn] Grants.gov fetch failed: {e}", file=sys.stderr)

    # NIH Guide FOAs RSS (global feed; filter via keywords)
    nih_feeds = [
        "https://grants.nih.gov/grants/guide/rss/nih-guide.xml"
    ]
    for url in nih_feeds:
        try:
            items = fetch_rss(url, "NIH Guide")
            all_items += [i for i in items if any(kw.lower() in (i["title"]+" "+i["description"]).lower() for kw in keywords)]
        except Exception as e:
            print(f"[warn] NIH RSS failed: {e}", file=sys.stderr)

    # NSF funding RSS
    try:
        nsf_feed = "https://www.nsf.gov/rss/rss_www_funding.xml"
        items = fetch_rss(nsf_feed, "NSF Funding")
        all_items += [i for i in items if any(kw.lower() in (i["title"]+" "+i["description"]).lower() for kw in keywords)]
    except Exception as e:
        print(f"[warn] NSF RSS failed: {e}", file=sys.stderr)

    # Score and sort
    for itm in all_items:
        itm["hbcu_msi_score"] = score_item(itm, keywords)

    # De-duplicate by URL
    seen = set()
    deduped = []
    for i in all_items:
        key = i.get("url") or i.get("id")
        if key in seen: 
            continue
        seen.add(key)
        deduped.append(i)

    deduped.sort(key=lambda x: x.get("hbcu_msi_score",0), reverse=True)

    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(deduped, f, indent=2)

    print(f"Wrote {len(deduped)} items to {args.out}")

if __name__ == "__main__":
    main()
