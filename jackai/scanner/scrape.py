"""Scrape: collect page URLs from seeds, optional crawl or sitemap."""

import re
from urllib.parse import urljoin, urlparse

import httpx

from jackai.models.scanner import ScrapeInput, ScrapeResult


def _same_origin(base_url: str, link: str) -> bool:
    base = urlparse(base_url)
    parsed = urlparse(link)
    if not parsed.netloc:
        return True
    return parsed.netloc == base.netloc and parsed.scheme == base.scheme


def _normalize_url(url: str) -> str:
    parsed = urlparse(url)
    if not parsed.scheme:
        return "https://" + url
    return url


def run_scrape(input_data: ScrapeInput) -> ScrapeResult:
    """
    Collect URLs from seeds. Optionally crawl same-origin links or use sitemap.
    """
    seen: set[str] = set()
    urls: list[str] = []

    for raw in input_data.seeds:
        u = _normalize_url(raw.strip())
        if u and u not in seen:
            seen.add(u)
            urls.append(u)

    if input_data.use_sitemap and urls:
        # Try sitemap for first seed's origin
        base = urlparse(urls[0])
        sitemap_url = f"{base.scheme}://{base.netloc}/sitemap.xml"
        try:
            with httpx.Client(follow_redirects=True, timeout=15) as client:
                r = client.get(sitemap_url)
                if r.status_code == 200 and "xml" in (r.headers.get("content-type") or ""):
                    # Simple extract <loc>...</loc>
                    for m in re.finditer(r"<loc>\s*([^<]+)\s*</loc>", r.text, re.I):
                        loc = m.group(1).strip()
                        if loc and loc not in seen and _same_origin(urls[0], loc):
                            seen.add(loc)
                            urls.append(loc)
        except Exception:
            pass

    if input_data.crawl_depth > 0 and urls:
        # Crawl: visit each URL, extract same-origin links, up to depth
        to_visit = [(u, 0) for u in urls]
        base_url = urls[0]

        try:
            from playwright.sync_api import sync_playwright
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                try:
                    while to_visit:
                        current, depth = to_visit.pop(0)
                        if depth > input_data.crawl_depth:
                            continue
                        try:
                            page = browser.new_page()
                            page.goto(current, wait_until="domcontentloaded", timeout=15000)
                            hrefs = page.evaluate("""() => {
                                const links = Array.from(document.querySelectorAll('a[href]'));
                                return links.map(a => a.href);
                            }""")
                            page.close()
                            for href in hrefs:
                                if not href:
                                    continue
                                href = href.split("#")[0].rstrip("/")
                                if _same_origin(base_url, href) and href not in seen:
                                    seen.add(href)
                                    urls.append(href)
                                    if depth + 1 <= input_data.crawl_depth:
                                        to_visit.append((href, depth + 1))
                        except Exception:
                            continue
                finally:
                    browser.close()
        except Exception:
            pass

    return ScrapeResult(urls=urls)
