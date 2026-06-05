#!/usr/bin/env python3
"""
Product Hunt Weekly Scraper & Analyzer
=======================================
Runs every Friday. Fully automated — no manual steps.

What it does:
  1. Fetches the Product Hunt RSS feed
  2. Appends new products to products.csv
  3. Scores unanalyzed products (opportunity 0-10, market viability 0-10)
  4. Full-analyses those scoring >= 6
  5. Appends results to analysis_history.csv
  6. Updates the live Google Sheet via Apps Script web app
  7. Marks all scored products in analyzed_ids.csv
  8. Commits and pushes all changes to main

Requirements:
  pip install requests feedparser python-dotenv

Environment variables (set in .env or shell):
  SHEETS_WEBAPP_URL  — /exec URL of the deployed sheets_webapp.gs web app

Usage:
  python weekly_scrape.py
"""

import csv
import os
import re
import subprocess
import sys
from datetime import datetime, timezone

# ── optional .env loading ─────────────────────────────────────────────────────
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

try:
    import requests
    import feedparser
except ImportError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "-q", "requests", "feedparser"])
    import requests
    import feedparser

from sheets_append import append_rows, smoke_test

# ── config ────────────────────────────────────────────────────────────────────
BASE         = os.path.dirname(os.path.abspath(__file__))
NOW          = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000Z")
DATE         = datetime.now(timezone.utc).strftime("%Y-%m-%d")
FEED_URL     = "https://www.producthunt.com/feed"
PRODUCTS_CSV = os.path.join(BASE, "products.csv")
ANALYZED_CSV = os.path.join(BASE, "analyzed_ids.csv")
HISTORY_CSV  = os.path.join(BASE, "analysis_history.csv")

HISTORY_HEADERS = [
    "product_id", "product_name", "product_url", "category", "value_proposition",
    "target_audience", "pain_points", "improvement_opportunities", "feature_gaps",
    "competitors", "market_viability_score", "opportunity_score",
    "differentiation_strategies", "technical_complexity", "estimated_build_time",
    "monetization_ideas", "red_flags", "recommended_approach", "key_insights",
    "analyzed_at",
]

# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def strip_html(text: str) -> str:
    return re.sub(r"<[^>]+>", " ", text or "").strip()


def git(*args):
    result = subprocess.run(["git", "-C", BASE] + list(args),
                            capture_output=True, text=True)
    if result.returncode != 0:
        print(f"git {' '.join(args)} failed: {result.stderr.strip()}")
    return result.returncode == 0


def commit_and_push(message: str, files: list[str]):
    for f in files:
        git("add", f)
    git("commit", "-m", message)
    for attempt in range(4):
        if git("push", "-u", "origin", "main"):
            break
        wait = 2 ** attempt
        print(f"Push failed, retrying in {wait}s…")
        import time; time.sleep(wait)


# ─────────────────────────────────────────────────────────────────────────────
# STEP 1 — Fetch RSS feed
# ─────────────────────────────────────────────────────────────────────────────

def fetch_feed() -> list[dict]:
    print(f"\n[STEP 1] Fetching {FEED_URL}")
    feed = feedparser.parse(FEED_URL)
    entries = feed.entries
    print(f"  Feed entries found: {len(entries)}")

    seen_slugs = set()
    products = []
    for e in entries:
        # Extract post ID from id field like "tag:www.producthunt.com,2005:Post/1162995"
        post_id_match = re.search(r"/(\d+)$", e.get("id", ""))
        if not post_id_match:
            continue
        post_id = int(post_id_match.group(1))

        # Slug from link: https://www.producthunt.com/products/my-product → my-product
        link = e.get("link", "")
        slug_match = re.search(r"/products/([^/?#]+)", link)
        if not slug_match:
            slug_match = re.search(r"/posts/([^/?#]+)", link)
        if not slug_match:
            continue
        slug = slug_match.group(1)

        if slug in seen_slugs:
            continue
        seen_slugs.add(slug)

        raw_desc = strip_html(e.get("summary", "") or e.get("content", [{}])[0].get("value", ""))
        tagline  = raw_desc[:200]

        products.append({
            "id":              post_id,
            "name":            e.get("title", "").strip(),
            "slug":            slug,
            "url":             f"https://www.producthunt.com/posts/{slug}",
            "description":     raw_desc,
            "tagline":         tagline,
            "launch_date":     e.get("published", ""),
            "discovered_date": NOW,
            "scraped_at":      NOW,
            "status":          "new",
        })

    print(f"  Unique products parsed: {len(products)}")
    return products


# ─────────────────────────────────────────────────────────────────────────────
# STEP 2 — Update products.csv
# ─────────────────────────────────────────────────────────────────────────────

def update_products(products: list[dict]) -> list[dict]:
    print(f"\n[STEP 2] Updating products.csv")
    existing_slugs = set()
    with open(PRODUCTS_CSV, "r", encoding="utf-8-sig") as f:
        reader = csv.reader(f)
        next(reader)
        for row in reader:
            if len(row) > 3:
                existing_slugs.add(row[3].strip())

    new_products = [p for p in products if p["slug"] not in existing_slugs]

    if new_products:
        with open(PRODUCTS_CSV, "a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            for p in new_products:
                writer.writerow([
                    str(p["id"]), p["url"], p["name"], p["slug"],
                    p["description"], p["tagline"],
                    "0", "0",
                    NOW, p["launch_date"], "new",
                    "", "",
                    NOW,
                    "", "", "", "",
                    NOW, NOW,
                ])
        print(f"  Added {len(new_products)} new product(s): {[p['name'] for p in new_products]}")
        commit_and_push(
            f"Scrape {DATE}: added {len(new_products)} product(s)",
            [PRODUCTS_CSV],
        )
    else:
        print("  No new products — products.csv unchanged")

    return new_products


# ─────────────────────────────────────────────────────────────────────────────
# STEP 3 — Filter unanalyzed products
# ─────────────────────────────────────────────────────────────────────────────

def filter_unanalyzed(products: list[dict]) -> list[dict]:
    print(f"\n[STEP 3] Filtering unanalyzed products")
    analyzed_ids = set()
    with open(ANALYZED_CSV, "r", encoding="utf-8-sig") as f:
        reader = csv.reader(f)
        next(reader)
        for row in reader:
            if row and row[0].strip():
                analyzed_ids.add(row[0].strip())

    unanalyzed = [p for p in products if str(p["id"]) not in analyzed_ids]
    print(f"  Unanalyzed: {len(unanalyzed)} of {len(products)}")
    for p in unanalyzed:
        print(f"    {p['id']} — {p['name']}")
    return unanalyzed


# ─────────────────────────────────────────────────────────────────────────────
# STEP 4 — Pass 1: Quick Scoring  (LLM-based via Claude API)
# ─────────────────────────────────────────────────────────────────────────────

def score_products(products: list[dict]) -> tuple[list[dict], list[dict]]:
    """Score each product. Returns (passing, failing)."""
    print(f"\n[STEP 4] Pass 1: Quick scoring {len(products)} product(s)")

    try:
        import anthropic
    except ImportError:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-q", "anthropic"])
        import anthropic

    client = anthropic.Anthropic()

    scored = []
    for p in products:
        prompt = f"""Score this Product Hunt launch as a SaaS replication opportunity.

Product: {p['name']}
Description: {p['description']}

Return ONLY valid JSON with these exact keys:
{{
  "opportunity_score": <0-10 integer>,
  "market_viability_score": <0-10 integer>,
  "technical_complexity": "<low|medium|high>"
}}

Scoring criteria:
- opportunity_score: How strong is this as a SaaS replication target? (10 = obvious, large, defensible market gap; 0 = not replicable)
- market_viability_score: How strong is the market demand? (10 = proven massive demand; 0 = no clear market)
- technical_complexity: How hard to build an MVP? (low = days, medium = weeks, high = months)"""

        try:
            msg = client.messages.create(
                model="claude-haiku-4-5-20251001",
                max_tokens=200,
                messages=[{"role": "user", "content": prompt}],
            )
            raw = msg.content[0].text.strip()
            # Extract JSON even if wrapped in markdown
            json_match = re.search(r"\{[^}]+\}", raw, re.DOTALL)
            if json_match:
                import json
                scores = json.loads(json_match.group())
                p.update(scores)
                result = "PASS" if scores["opportunity_score"] >= 6 else "FAIL"
                print(f"  {result} {p['id']} {p['name']}: opp={scores['opportunity_score']}, mkt={scores['market_viability_score']}, complexity={scores['technical_complexity']}")
            else:
                print(f"  SKIP {p['id']} {p['name']}: could not parse scores")
                p["opportunity_score"] = 0
                p["market_viability_score"] = 0
                p["technical_complexity"] = "high"
        except Exception as ex:
            print(f"  ERROR scoring {p['name']}: {ex}")
            p["opportunity_score"] = 0
            p["market_viability_score"] = 0
            p["technical_complexity"] = "high"

        scored.append(p)

    passing = [p for p in scored if p.get("opportunity_score", 0) >= 6]
    failing = [p for p in scored if p.get("opportunity_score", 0) < 6]
    print(f"  Passed: {len(passing)}  Failed: {len(failing)}")
    return passing, failing


# ─────────────────────────────────────────────────────────────────────────────
# STEP 5 — Pass 2: Full Analysis
# ─────────────────────────────────────────────────────────────────────────────

def analyze_product(p: dict, client) -> dict:
    prompt = f"""You are a SaaS market analyst. Produce a full opportunity analysis for this Product Hunt launch.

Product: {p['name']}
URL: {p['url']}
Description: {p['description']}
Opportunity score: {p['opportunity_score']}/10
Market viability: {p['market_viability_score']}/10
Technical complexity: {p['technical_complexity']}

Return ONLY valid JSON with exactly these keys (no extra keys, no markdown):
{{
  "category": "<product category>",
  "value_proposition": "<1-2 sentences>",
  "target_audience": "<description>",
  "pain_points": "1. ...\\n2. ...\\n3. ...",
  "improvement_opportunities": "1. ...\\n2. ...\\n3. ...",
  "feature_gaps": "1. ...\\n2. ...\\n3. ...",
  "competitors": "1. ...\\n2. ...\\n3. ...",
  "differentiation_strategies": "1. ...\\n2. ...\\n3. ...",
  "monetization_ideas": "1. ...\\n2. ...\\n3. ...",
  "red_flags": "1. ...\\n2. ...\\n3. ...",
  "estimated_build_time": "<e.g. 8-12 weeks>",
  "recommended_approach": "<one paragraph>",
  "key_insights": "<one sentence>"
}}"""

    import json
    msg = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=2000,
        messages=[{"role": "user", "content": prompt}],
    )
    raw = msg.content[0].text.strip()
    # Strip markdown code fences if present
    raw = re.sub(r"^```(?:json)?\s*", "", raw)
    raw = re.sub(r"\s*```$", "", raw)

    analysis = json.loads(raw)
    analysis.update({
        "product_id":              p["id"],
        "product_name":            p["name"],
        "product_url":             p["url"],
        "market_viability_score":  p["market_viability_score"],
        "opportunity_score":       p["opportunity_score"],
        "technical_complexity":    p["technical_complexity"],
        "analyzed_at":             NOW,
    })
    return analysis


def full_analysis(passing: list[dict]) -> list[dict]:
    print(f"\n[STEP 5] Pass 2: Full analysis on {len(passing)} product(s)")
    if not passing:
        return []

    try:
        import anthropic
    except ImportError:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-q", "anthropic"])
        import anthropic

    client = anthropic.Anthropic()
    analyses = []
    for p in passing:
        try:
            a = analyze_product(p, client)
            analyses.append(a)
            print(f"  Analyzed: {p['name']}")
        except Exception as ex:
            print(f"  ERROR analyzing {p['name']}: {ex}")

    return analyses


# ─────────────────────────────────────────────────────────────────────────────
# STEP 6 — Save results
# ─────────────────────────────────────────────────────────────────────────────

def save_results(analyses: list[dict], all_scored: list[dict]):
    print(f"\n[STEP 6] Saving results")

    # 6A — analysis_history.csv
    if analyses:
        with open(HISTORY_CSV, "a", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=HISTORY_HEADERS, extrasaction="ignore")
            for a in analyses:
                writer.writerow(a)
        print(f"  analysis_history.csv: appended {len(analyses)} row(s)")
        commit_and_push(
            f"Analysis {DATE}: {len(analyses)} product(s) analyzed",
            [HISTORY_CSV],
        )

    # 6B — Google Sheet (via Apps Script web app)
    if analyses:
        try:
            smoke_test()
            append_rows(analyses, HISTORY_HEADERS)
        except EnvironmentError as e:
            print(f"  [WARN] Skipping Sheets update: {e}")
        except Exception as ex:
            print(f"  [WARN] Sheets update failed: {ex}")

    # 6C — analyzed_ids.csv (all scored, pass + fail)
    if all_scored:
        existing_ids = set()
        with open(ANALYZED_CSV, "r", encoding="utf-8-sig") as f:
            reader = csv.reader(f)
            next(reader)
            for row in reader:
                if row and row[0].strip():
                    existing_ids.add(row[0].strip())

        new_ids = [p for p in all_scored if str(p["id"]) not in existing_ids]
        if new_ids:
            with open(ANALYZED_CSV, "a", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                for p in new_ids:
                    writer.writerow([str(p["id"])] + [""] * 19)
            print(f"  analyzed_ids.csv: marked {len(new_ids)} product(s)")
            commit_and_push(
                f"Mark {len(new_ids)} products as analyzed {DATE}",
                [ANALYZED_CSV],
            )
        else:
            print("  analyzed_ids.csv: nothing new to mark")


# ─────────────────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────────────────

def main():
    print(f"=== Product Hunt Weekly Scrape — {DATE} ===")

    products   = fetch_feed()
    _new       = update_products(products)
    unanalyzed = filter_unanalyzed(products)

    if not unanalyzed:
        print("\nAll products already analyzed. Nothing to do.")
        return

    passing, failing = score_products(unanalyzed)
    all_scored = passing + failing

    if not passing:
        print("\nNo products scored >= 6. Updating analyzed_ids.csv and stopping.")
        save_results([], all_scored)
        return

    analyses = full_analysis(passing)
    save_results(analyses, all_scored)

    print(f"\n=== Done — {len(analyses)} product(s) analyzed ===")
    for a in analyses:
        print(f"  [{a['opportunity_score']}/10] {a['product_name']} — {a.get('category', '')}")


if __name__ == "__main__":
    main()
