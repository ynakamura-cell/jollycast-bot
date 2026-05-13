"""
Build Zendesk cache using Playwright (headless Chrome).
Run once: python build_cache.py
"""
import json, time, subprocess, sys
from pathlib import Path

CACHE = Path(__file__).parent / "zendesk_cache.json"

# 重要カテゴリ（トラブル・初めてのお仕事・日程変更・サービス）
CATEGORY_URLS = [
    "https://casy.zendesk.com/hc/ja/categories/900000219206",  # トラブルが起こったら
    "https://casy.zendesk.com/hc/ja/categories/900000219166",  # 初めてのお仕事に向けて
    "https://casy.zendesk.com/hc/ja/categories/900000219186",  # 日程変更やキャンセル
    "https://casy.zendesk.com/hc/ja/categories/900001211883",  # CaSyのサービス
    "https://casy.zendesk.com/hc/ja/categories/900001211943",  # サポート
    "https://casy.zendesk.com/hc/ja/categories/900001211903",  # スキルアップポイント
]

def fetch_with_playwright():
    script = '''
import asyncio, json
from playwright.async_api import async_playwright

CATEGORIES = ''' + json.dumps(CATEGORY_URLS) + '''

async def get_text(page, url):
    try:
        await page.goto(url, timeout=15000, wait_until="domcontentloaded")
        await asyncio.sleep(0.5)
        return await page.content()
    except:
        return ""

async def main():
    articles = []
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        # Collect section links
        section_urls = set()
        for cat_url in CATEGORIES:
            html = await get_text(page, cat_url)
            import re
            sections = re.findall(r\'href="(/hc/ja/sections/[^"]+)"\', html)
            for s in sections:
                section_urls.add("https://casy.zendesk.com" + s)

        print(f"Sections: {len(section_urls)}", flush=True)

        # Collect article links
        article_urls = set()
        for sec_url in section_urls:
            html = await get_text(page, sec_url)
            import re
            arts = re.findall(r\'href="(/hc/ja/articles/[^"#]+)"\', html)
            for a in arts:
                article_urls.add("https://casy.zendesk.com" + a)

        print(f"Articles: {len(article_urls)}", flush=True)

        # Fetch each article
        for url in list(article_urls)[:60]:
            try:
                await page.goto(url, timeout=15000, wait_until="domcontentloaded")
                await asyncio.sleep(0.3)

                title = await page.title()
                title = title.replace(" – 株式会社CaSy", "").strip()

                # Get article body text
                el = page.locator("article").first
                try:
                    content = await el.inner_text(timeout=3000)
                except:
                    content = await page.locator("main").inner_text()

                content = " ".join(content.split())[:2500]
                if len(content) > 80:
                    articles.append({"url": url, "title": title, "content": content})
                    print(f"  + {title[:50]}", flush=True)
            except Exception as e:
                pass

        await browser.close()

    print(json.dumps(articles, ensure_ascii=False))

asyncio.run(main())
'''
    result = subprocess.run(
        [sys.executable, "-c", script],
        capture_output=True, text=True, timeout=300
    )

    # Last line is JSON
    lines = result.stdout.strip().split("\n")
    json_line = None
    log_lines = []
    for line in lines:
        if line.startswith("["):
            json_line = line
        else:
            log_lines.append(line)

    for l in log_lines:
        print(l)

    if json_line:
        return json.loads(json_line)
    return []


def fetch_with_requests():
    """Fallback: requests with browser headers."""
    import urllib.request
    import re

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "ja,en-US;q=0.9",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
    }

    def fetch(url):
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=12) as r:
                import gzip
                raw = r.read()
                try:
                    return gzip.decompress(raw).decode("utf-8", errors="replace")
                except Exception:
                    return raw.decode("utf-8", errors="replace")
        except Exception as e:
            print(f"  SKIP {url}: {e}")
            return ""

    section_urls = set()
    for cat_url in CATEGORY_URLS:
        html = fetch(cat_url)
        sections = re.findall(r'href="(/hc/ja/sections/[^"]+)"', html)
        for s in sections:
            section_urls.add("https://casy.zendesk.com" + s)
        time.sleep(0.3)
    print(f"Sections: {len(section_urls)}")

    article_urls = set()
    for sec_url in section_urls:
        html = fetch(sec_url)
        arts = re.findall(r'href="(/hc/ja/articles/[^"#]+)"', html)
        for a in arts:
            article_urls.add("https://casy.zendesk.com" + a)
        time.sleep(0.3)
    print(f"Articles: {len(article_urls)}")

    articles = []
    for url in list(article_urls)[:60]:
        html = fetch(url)
        if not html:
            continue
        title_m = re.search(r"<h1[^>]*>(.*?)</h1>", html, re.DOTALL)
        title = re.sub(r"<[^>]+>", "", title_m.group(1)).strip() if title_m else url
        body_m = re.search(r"<article[^>]*>(.*?)</article>", html, re.DOTALL)
        body = body_m.group(1) if body_m else html
        content = re.sub(r"<[^>]+>", " ", body)
        content = re.sub(r"\s+", " ", content).strip()[:2500]
        if len(content) > 80:
            articles.append({"url": url, "title": title, "content": content})
            print(f"  + {title[:50]}")
        time.sleep(0.3)
    return articles


if __name__ == "__main__":
    # Try playwright first, fall back to requests
    articles = []
    try:
        import playwright
        print("Using Playwright...")
        articles = fetch_with_playwright()
    except ImportError:
        print("Playwright not available, using requests...")
        articles = fetch_with_requests()

    CACHE.write_text(json.dumps(articles, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nDone: {len(articles)} articles saved to cache.")
