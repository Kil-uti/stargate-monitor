"""
Energy-AI Infrastructure News Monitor
Runs in GitHub Actions and writes output for GitHub Pages.

Outputs:
- docs/data/articles_latest.json
- docs/data/articles_latest.csv
- docs/data/archive/articles_<timestamp>.json
- docs/data/archive/articles_<timestamp>.csv
"""

import csv
import json
import os
import re
from datetime import datetime, timezone
from typing import Dict, List, Tuple

import feedparser
import requests


# =========================
# CONFIG
# =========================
FEEDS: Dict[str, str] = {
    "TechCrunch AI": "https://techcrunch.com/category/artificial-intelligence/feed/",
    "Data Center Dynamics": "https://www.datacenterdynamics.com/en/rss/",
    "Utility Dive": "https://www.utilitydive.com/feeds/news/",
    "FERC News": "https://www.ferc.gov/news-events/news/rss",
    "World Nuclear News": "https://www.world-nuclear-news.org/rss",
}

MAX_PER_FEED = 20

OUTPUT_DIR = os.path.join("docs", "data")
ARCHIVE_DIR = os.path.join(OUTPUT_DIR, "archive")

LATEST_JSON = os.path.join(OUTPUT_DIR, "articles_latest.json")
LATEST_CSV = os.path.join(OUTPUT_DIR, "articles_latest.csv")


# =========================
# RELEVANCE FILTER
# =========================
def is_relevant(title: str, description: str) -> Tuple[bool, str]:
    text = f"{title} {description}".lower()

    negative_keywords = [
        "tv show", "sci-fi", "sg-1", "atlantis", "television",
        "cryptocurrency", "$stg", "defi", "token", "blockchain",
    ]
    for kw in negative_keywords:
        if kw in text:
            return False, f"Filtered: {kw}"

    stargate_terms = [
        "stargate project", "stargate ai", "openai data center", "project stargate"
    ]
    ai_terms = [
        "ai data center", "artificial intelligence infrastructure", "hyperscale",
        "gpu cluster", "compute cluster", "data center", "datacenter",
    ]
    energy_terms = [
        "grid capacity", "power demand", "electricity", "transmission",
        "interconnection", "substation", "pjm", "ercot", "nyiso", "iso-ne",
        "ferc", "capacity market", "nuclear", "gas plant", "power plant",
    ]

    if any(term in text for term in stargate_terms):
        return True, "Stargate mention"

    has_ai = ("ai" in text) or any(term in text for term in ai_terms)
    has_energy = any(term in text for term in energy_terms)
    if has_ai and has_energy:
        return True, "AI + Energy nexus"

    if any(term in text for term in ["grid", "capacity", "interconnection", "data center", "datacenter"]):
        return True, "Infrastructure mention"

    return False, "No relevant keywords"


# =========================
# FEED FETCHING (robust)
# =========================
def fetch_feed(url: str) -> feedparser.FeedParserDict:
    headers = {
        "User-Agent": "Mozilla/5.0 (compatible; StargateMonitor/1.0; +https://github.com/)"
    }
    try:
        r = requests.get(url, headers=headers, timeout=25)
        r.raise_for_status()
        return feedparser.parse(r.content)
    except Exception:
        # fallback
        return feedparser.parse(url)


def clean_html(text: str) -> str:
    text = re.sub(r"<[^<]+?>", "", text or "")
    text = re.sub(r"\s+", " ", text).strip()
    return text


def collect_articles() -> List[dict]:
    all_articles: List[dict] = []

    print("Starting news collection...")
    print("=" * 60)

    for source_name, feed_url in FEEDS.items():
        print(f"\n📡 Fetching: {source_name}")
        try:
            feed = fetch_feed(feed_url)
            if getattr(feed, "bozo", False):
                print("   ⚠️  Warning: Feed may have issues")

            count = 0
            for entry in (feed.entries or [])[:MAX_PER_FEED]:
                title = entry.get("title", "No title")
                link = entry.get("link", "")
                published = entry.get("published") or entry.get("updated") or "Unknown date"
                summary = entry.get("summary") or entry.get("description") or ""
                summary_clean = clean_html(summary)[:350]

                relevant, reason = is_relevant(title, summary_clean)

                all_articles.append(
                    {
                        "source": source_name,
                        "title": title,
                        "link": link,
                        "published": published,
                        "summary": summary_clean,
                        "relevant": relevant,
                        "reason": reason,
                    }
                )
                count += 1

            print(f"   ✅ Collected {count} articles")

        except Exception as e:
            print(f"   ❌ Error: {str(e)}")

    return all_articles


def ensure_dirs():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    os.makedirs(ARCHIVE_DIR, exist_ok=True)


def write_csv(path: str, articles: List[dict]) -> None:
    fieldnames = ["source", "title", "link", "published", "relevant", "reason", "summary"]
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        for a in articles:
            row = dict(a)
            row["relevant"] = "True" if a.get("relevant") else "False"
            w.writerow(row)


def write_json(path: str, payload: dict) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)


def main():
    print("⚡ Energy-AI Infrastructure News Monitor")
    print("   GitHub Actions / Pages mode\n")

    ensure_dirs()
    articles = collect_articles()

    total = len(articles)
    relevant_count = sum(1 for a in articles if a.get("relevant"))
    filtered = total - relevant_count

    now_utc = datetime.now(timezone.utc)
    ts = now_utc.strftime("%Y%m%d_%H%M%S")
    archive_csv = os.path.join(ARCHIVE_DIR, f"articles_{ts}.csv")
    archive_json = os.path.join(ARCHIVE_DIR, f"articles_{ts}.json")

    payload = {
        "generated_utc": now_utc.isoformat(),
        "total": total,
        "relevant": relevant_count,
        "filtered": filtered,
        "articles": [
            {
                **a,
                "relevant": "True" if a.get("relevant") else "False",
            }
            for a in articles
        ],
    }

    # write archive
    write_csv(archive_csv, articles)
    write_json(archive_json, payload)

    # write latest
    write_csv(LATEST_CSV, articles)
    write_json(LATEST_JSON, payload)

    print("\n" + "=" * 60)
    print("COLLECTION STATISTICS")
    print("=" * 60)
    print(f"Total articles collected: {total}")
    print(f"Relevant articles:        {relevant_count} ({(relevant_count/total*100 if total else 0):.1f}%)")
    print(f"Filtered out:             {filtered} ({(filtered/total*100 if total else 0):.1f}%)")
    print("=" * 60)

    print(f"\n💾 Wrote: {LATEST_JSON}")
    print(f"💾 Wrote: {LATEST_CSV}")
    print("\n✅ Done.")


if __name__ == "__main__":
    main()
