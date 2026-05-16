"""
Fetches and caches articles from the CaSy Zendesk help center.

Discovery flow:
  1. Crawl /hc/ja home page → category links  (static HTML, no auth needed)
  2. Crawl each category page → section links  (static HTML, no auth needed)
  3. Call /api/v2/help_center/ja/sections/{id}/articles.json per section
     → article IDs (bypasses JS-rendered section pages)
  4. Fetch each /hc/ja/articles/{id} page → extract body text

Optional authentication (set in .env to access drafts or private articles):
  ZENDESK_EMAIL + ZENDESK_API_TOKEN  (Basic auth, recommended)
  ZENDESK_SESSION_COOKIE             (session cookie fallback)
"""
import json, time, re, os, base64
from pathlib import Path
import urllib.request

BASE = "https://casy.zendesk.com"
HOME = f"{BASE}/hc/ja"
CACHE = Path(__file__).parent / "zendesk_cache.json"


def _auth_header() -> dict:
    email = os.getenv("ZENDESK_EMAIL", "")
    token = os.getenv("ZENDESK_API_TOKEN", "")
    if email and token:
        cred = base64.b64encode(f"{email}/token:{token}".encode()).decode()
        return {"Authorization": f"Basic {cred}"}
    cookie = os.getenv("ZENDESK_SESSION_COOKIE", "")
    if cookie:
        return {"Cookie": f"_zendesk_session={cookie}"}
    return {}


def _fetch_html(url: str) -> str:
    headers = {"User-Agent": "Mozilla/5.0", **_auth_header()}
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=12) as r:
            return r.read().decode("utf-8", errors="replace")
    except Exception as e:
        print(f"  [html error] {url}: {e}")
        return ""


def _fetch_json(url: str) -> dict | None:
    headers = {"User-Agent": "Mozilla/5.0", "Accept": "application/json", **_auth_header()}
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=12) as r:
            return json.loads(r.read().decode("utf-8"))
    except Exception as e:
        print(f"  [api error] {url}: {e}")
        return None


def _extract_links(html: str, pattern: str) -> list[str]:
    seen, out = set(), []
    for href in re.findall(pattern, html):
        url = href if href.startswith("http") else BASE + href
        if url not in seen:
            seen.add(url)
            out.append(url)
    return out


def _html_to_text(html: str) -> str:
    html = re.sub(r"<(script|style)[^>]*>.*?</\1>", "", html, flags=re.DOTALL)
    text = re.sub(r"<[^>]+>", " ", html)
    return re.sub(r"\s+", " ", text).strip()


def build_knowledge_base(force_refresh: bool = False) -> list[dict]:
    if CACHE.exists() and not force_refresh:
        data = json.loads(CACHE.read_text(encoding="utf-8"))
        if data:
            return data

    print("Fetching Zendesk articles (hybrid crawler)...")

    # Step 1: category links from home page
    home_html = _fetch_html(HOME)
    category_links = _extract_links(home_html, r'href="(/hc/ja/categories/[^"]+)"')
    print(f"  Step 1: {len(category_links)} categories")

    # Step 2: section links from each category page
    section_ids: list[str] = []
    seen_sections: set[str] = set()
    for cat_url in category_links:
        cat_html = _fetch_html(cat_url)
        sections = _extract_links(cat_html, r'href="(/hc/ja/sections/[^"]+)"')
        for sec_url in sections:
            m = re.search(r"/sections/(\d+)", sec_url)
            if m and m.group(1) not in seen_sections:
                seen_sections.add(m.group(1))
                section_ids.append(m.group(1))
        time.sleep(0.2)
    print(f"  Step 2: {len(section_ids)} sections")

    # Step 3: article IDs via API (avoids JS-rendered section pages)
    article_ids: list[str] = []
    seen_ids: set[str] = set()
    for sec_id in section_ids:
        url = f"{BASE}/api/v2/help_center/ja/sections/{sec_id}/articles.json?per_page=100"
        while url:
            data = _fetch_json(url)
            if not data:
                break
            for art in data.get("articles", []):
                aid = str(art["id"])
                if aid not in seen_ids and not art.get("draft", False):
                    seen_ids.add(aid)
                    article_ids.append(aid)
            url = data.get("next_page")
        time.sleep(0.2)
    print(f"  Step 3: {len(article_ids)} article IDs")

    # Step 4: fetch each article page and extract body text
    articles = []
    for aid in article_ids:
        art_url = f"{BASE}/hc/ja/articles/{aid}"
        html = _fetch_html(art_url)
        if not html:
            continue

        title_m = re.search(r"<h1[^>]*>(.*?)</h1>", html, re.DOTALL)
        title = re.sub(r"<[^>]+>", "", title_m.group(1)).strip() if title_m else art_url

        body_m = re.search(r"<article[^>]*>(.*?)</article>", html, re.DOTALL)
        body_html = body_m.group(1) if body_m else html
        content = _html_to_text(body_html)[:8000]

        if len(content) > 80:
            articles.append({"url": art_url, "title": title, "content": content})
            print(f"    + {title[:60]}")
        time.sleep(0.25)

    if articles:
        CACHE.write_text(
            json.dumps(articles, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        print(f"  Saved {len(articles)} articles.")
    else:
        print("  No articles fetched. Check network access.")

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
