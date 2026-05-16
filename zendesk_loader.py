"""
Fetches and caches articles from the CaSy Zendesk help center.

Authentication: Uses Zendesk REST API with email + API token.
Set in .env:
  ZENDESK_EMAIL=your@email.com
  ZENDESK_API_TOKEN=your_api_token

API token generation: Zendesk Admin > Profile (bottom-left) > API token

Falls back to the existing cache if credentials are not set.
"""
import json, time, re, os, base64
from pathlib import Path
import urllib.request

BASE = "https://casy.zendesk.com"
CACHE = Path(__file__).parent / "zendesk_cache.json"


def _get_auth_header() -> dict:
    """Returns Authorization header (API token) or Cookie header, whichever is set."""
    email = os.getenv("ZENDESK_EMAIL", "")
    token = os.getenv("ZENDESK_API_TOKEN", "")
    if email and token:
        credentials = f"{email}/token:{token}"
        encoded = base64.b64encode(credentials.encode()).decode()
        return {"Authorization": f"Basic {encoded}"}
    cookie = os.getenv("ZENDESK_SESSION_COOKIE", "")
    if cookie:
        return {"Cookie": f"_zendesk_session={cookie}"}
    return {}


def _fetch_api(url: str) -> dict | None:
    """Fetch a Zendesk API endpoint (JSON). Returns parsed dict or None on error."""
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Accept": "application/json",
        **_get_auth_header(),
    }
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=15) as r:
            return json.loads(r.read().decode("utf-8"))
    except Exception as e:
        print(f"  [API error] {url}: {e}")
        return None


def _html_to_text(html: str) -> str:
    html = re.sub(r"<(script|style)[^>]*>.*?</\1>", "", html, flags=re.DOTALL)
    text = re.sub(r"<[^>]+>", " ", html)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def build_knowledge_base(force_refresh: bool = False) -> list[dict]:
    if CACHE.exists() and not force_refresh:
        data = json.loads(CACHE.read_text(encoding="utf-8"))
        if data:
            return data

    email = os.getenv("ZENDESK_EMAIL", "")
    token = os.getenv("ZENDESK_API_TOKEN", "")
    cookie = os.getenv("ZENDESK_SESSION_COOKIE", "")

    if not (email and token) and not cookie:
        print(
            "WARNING: No Zendesk credentials in .env.\n"
            "  Set either:\n"
            "    ZENDESK_EMAIL + ZENDESK_API_TOKEN  (permanent, recommended)\n"
            "    ZENDESK_SESSION_COOKIE             (temporary, browser cookie)\n"
            "  Using existing cache if available."
        )
        if CACHE.exists():
            return json.loads(CACHE.read_text(encoding="utf-8"))
        return []

    print("Fetching Zendesk articles via API...")
    articles = []

    # Paginate through all articles
    url = f"{BASE}/api/v2/help_center/ja/articles.json?per_page=100&sort_by=created_at&sort_order=asc"
    page = 1
    while url:
        print(f"  Page {page}...", flush=True)
        data = _fetch_api(url)
        if not data:
            break

        for art in data.get("articles", []):
            if not art.get("draft", False):  # skip drafts
                body_html = art.get("body", "") or ""
                content = _html_to_text(body_html)[:8000]
                if len(content) > 80:
                    articles.append({
                        "url": f"{BASE}/hc/ja/articles/{art['id']}",
                        "title": art.get("title", ""),
                        "content": content,
                    })
                    print(f"    + {art.get('title', '')[:60]}")

        url = data.get("next_page")  # None when last page
        page += 1
        if url:
            time.sleep(0.3)

    if articles:
        CACHE.write_text(json.dumps(articles, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"  Saved {len(articles)} articles.")
    else:
        print("  No articles fetched. Check credentials and Zendesk permissions.")

    return articles


def search_articles(query: str, articles: list[dict], top_k: int = 3) -> list[dict]:
    q = query.lower()
    keyword_map = {
        "absent": "不在", "not home": "不在", "damage": "物損", "broke": "物損",
        "cancel": "キャンセル", "lost": "道迷い", "address": "住所",
        "key": "鍵", "schedule": "日程", "change": "変更", "voucher": "バウチャー",
        "qr": "QR", "late": "遅刻", "injury": "ケガ", "accident": "事故",
    }
    for en, ja in keyword_map.items():
        if en in q:
            q += " " + ja

    words = q.split()
    scored = []
    for art in articles:
        text = (art.get("title", "") + " " + art.get("content", "")).lower()
        score = sum(text.count(w) for w in words)
        if score > 0:
            scored.append((score, art))
    scored.sort(key=lambda x: x[0], reverse=True)
    return [a for _, a in scored[:top_k]]
