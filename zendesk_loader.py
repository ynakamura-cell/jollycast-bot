"""
Fetches and caches articles from the CaSy Zendesk help center.
Crawls from the home page — no guessed article IDs needed.
"""
import json, time, re
from pathlib import Path
import urllib.request

BASE = "https://casy.zendesk.com"
HOME = f"{BASE}/hc/ja"
CACHE = Path(__file__).parent / "zendesk_cache.json"


def _fetch(url: str) -> str:
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=10) as r:
            return r.read().decode("utf-8", errors="replace")
    except Exception:
        return ""


def _extract_links(html: str, pattern: str) -> list[str]:
    found = re.findall(pattern, html)
    seen, out = set(), []
    for href in found:
        url = href if href.startswith("http") else BASE + href
        if url not in seen:
            seen.add(url)
            out.append(url)
    return out


def _html_to_text(html: str) -> str:
    # Remove script/style blocks
    html = re.sub(r"<(script|style)[^>]*>.*?</\1>", "", html, flags=re.DOTALL)
    # Remove tags
    text = re.sub(r"<[^>]+>", " ", html)
    # Collapse whitespace
    text = re.sub(r"\s+", " ", text).strip()
    return text


def build_knowledge_base(force_refresh: bool = False) -> list[dict]:
    if CACHE.exists() and not force_refresh:
        data = json.loads(CACHE.read_text(encoding="utf-8"))
        if data:
            return data

    print("Fetching Zendesk articles...")
    articles = []

    # Step 1: Get category links from home page
    home_html = _fetch(HOME)
    category_links = _extract_links(home_html, r'href="(/hc/ja/categories/[^"]+)"')
    print(f"  Found {len(category_links)} categories")

    # Step 2: Get section links from each category
    section_links = []
    for cat_url in category_links:
        cat_html = _fetch(cat_url)
        sections = _extract_links(cat_html, r'href="(/hc/ja/sections/[^"]+)"')
        section_links.extend(sections)
        time.sleep(0.2)
    print(f"  Found {len(section_links)} sections")

    # Step 3: Get article links from each section
    article_urls = set()
    for sec_url in section_links:
        sec_html = _fetch(sec_url)
        arts = _extract_links(sec_html, r'href="(/hc/ja/articles/[^"#]+)"')
        article_urls.update(arts)
        time.sleep(0.2)
    print(f"  Found {len(article_urls)} article URLs")

    # Step 4: Fetch each article (no arbitrary cap — fetch all found articles)
    for url in list(article_urls):
        html = _fetch(url)
        if not html:
            continue
        title_m = re.search(r"<h1[^>]*>(.*?)</h1>", html, re.DOTALL)
        title = re.sub(r"<[^>]+>", "", title_m.group(1)).strip() if title_m else url

        # Extract article body only; 8000 chars covers most full articles
        body_m = re.search(r'<article[^>]*>(.*?)</article>', html, re.DOTALL)
        body_html = body_m.group(1) if body_m else html
        content = _html_to_text(body_html)[:8000]

        if len(content) > 80:
            articles.append({"url": url, "title": title, "content": content})
            print(f"    + {title[:50]}")
        time.sleep(0.25)

    CACHE.write_text(json.dumps(articles, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"  Saved {len(articles)} articles.")
    return articles


def search_articles(query: str, articles: list[dict], top_k: int = 3) -> list[dict]:
    q = query.lower()
    # Also check English keywords mapped to Japanese terms
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
