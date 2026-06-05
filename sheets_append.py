"""
Append rows to the live Google Sheet via the deployed Apps Script web app.

Usage:
    from sheets_append import append_rows
    append_rows(list_of_dicts, HEADERS)

Requires:
    SHEETS_WEBAPP_URL env var set to the /exec URL of the deployed web app.
    Install: pip install requests
"""

import os, json, requests

SPREADSHEET_URL = "https://docs.google.com/spreadsheets/d/15RMY2hV7cPU9QzFtmY_n_uW_wfAHK3nqiw7W2Lvi3GY/edit?gid=1725789762"
HEADERS = [
    "product_id", "product_name", "product_url", "category", "value_proposition",
    "target_audience", "pain_points", "improvement_opportunities", "feature_gaps",
    "competitors", "market_viability_score", "opportunity_score",
    "differentiation_strategies", "technical_complexity", "estimated_build_time",
    "monetization_ideas", "red_flags", "recommended_approach", "key_insights",
    "analyzed_at",
]


def _get_webapp_url():
    url = os.environ.get("SHEETS_WEBAPP_URL", "").strip()
    if not url:
        raise EnvironmentError(
            "SHEETS_WEBAPP_URL is not set.\n"
            "Deploy sheets_webapp.gs as a Google Apps Script web app, then:\n"
            "  export SHEETS_WEBAPP_URL='https://script.google.com/macros/s/.../exec'"
        )
    return url


def append_rows(analyses: list[dict], headers: list[str] = HEADERS) -> dict:
    """
    POST a list of analysis dicts to the Apps Script web app.
    Each dict is converted to an ordered list matching `headers`.
    Returns the JSON response from the web app.
    """
    webapp_url = _get_webapp_url()
    rows = [[str(a.get(h, "")) for h in headers] for a in analyses]
    payload = {"rows": rows}

    resp = requests.post(webapp_url, json=payload, timeout=30)
    resp.raise_for_status()
    result = resp.json()

    if result.get("status") == "ok":
        print(f"Sheets: appended {result['appended']} row(s) → {SPREADSHEET_URL}")
    else:
        raise RuntimeError(f"Sheets append failed: {result}")

    return result


def smoke_test():
    """GET the web app to confirm it's live before running the full scrape."""
    webapp_url = _get_webapp_url()
    resp = requests.get(webapp_url, timeout=10)
    resp.raise_for_status()
    result = resp.json()
    print(f"Sheets web app: {result}")
    return result


if __name__ == "__main__":
    smoke_test()
