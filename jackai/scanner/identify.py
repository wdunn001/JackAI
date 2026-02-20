"""Identify: load page, detect chat widgets via signatures and heuristics, return IdentifiedInteraction[]."""

from urllib.parse import urlparse

from jackai.models.config import WebWidgetSelectors
from jackai.models.scanner import IdentifiedInteraction
from jackai.scanner.signatures import get_signatures


# Generic heuristics: selectors for unknown chat-like widgets
GENERIC_SELECTORS = WebWidgetSelectors(
    input_selector="[contenteditable='true'], textarea[placeholder*='message' i], input[type='text'][placeholder*='message' i]",
    message_list_selector="[class*='message'][class*='list'], [class*='chat'][class*='content'], [class*='conversation'], .messages, .chat-messages",
    send_selector="button[type='submit'], button[class*='send' i], [aria-label*='send' i]",
    widget_container_selector="[class*='chat'][class*='widget' i], [id*='chat' i], [class*='messenger']",
)


def _detect_by_signatures(page, base_url: str) -> list[IdentifiedInteraction]:
    """Detect widgets using known signature registry."""
    results: list[IdentifiedInteraction] = []
    for sig in get_signatures():
        try:
            if sig.script_selector and not page.locator(sig.script_selector).first.count():
                continue
            frame = page
            if sig.iframe_selector:
                if not page.locator(sig.iframe_selector).first.count():
                    continue
                frame_el = page.locator(sig.iframe_selector).first
                frame = frame_el.content_frame()
                if not frame:
                    continue
            # Check that input exists in (possibly iframe) context
            inp = frame.locator(sig.selectors.input_selector).first
            if inp.count() == 0:
                continue
            msg_list = frame.locator(sig.selectors.message_list_selector).first
            if msg_list.count() == 0:
                continue
            results.append(
                IdentifiedInteraction(
                    url=base_url,
                    widget_type=sig.provider,
                    selectors=sig.selectors,
                    confidence=0.9,
                    frame=sig.iframe_selector,
                )
            )
        except Exception:
            continue
    return results


def _detect_by_heuristics(page, base_url: str) -> list[IdentifiedInteraction]:
    """Detect chat-like containers by heuristics (chat in id/class, input + send)."""
    results: list[IdentifiedInteraction] = []
    try:
        # Look for chat-like containers
        candidates = page.locator(
            "[class*='chat' i], [id*='chat' i], [class*='messenger' i], [class*='widget' i]"
        ).all()
        for el in candidates:
            try:
                inp = el.locator(GENERIC_SELECTORS.input_selector).first
                if inp.count() == 0:
                    continue
                msg_list = el.locator(GENERIC_SELECTORS.message_list_selector).first
                if msg_list.count() == 0:
                    msg_sel = el.locator("[class*='message' i], [class*='bubble' i], .msg, li, p").first
                    if msg_sel.count() == 0:
                        continue
                    selectors = WebWidgetSelectors(
                        input_selector=GENERIC_SELECTORS.input_selector,
                        message_list_selector="[class*='message' i], [class*='bubble' i], .msg, li, p",
                        send_selector=GENERIC_SELECTORS.send_selector,
                        widget_container_selector=GENERIC_SELECTORS.widget_container_selector,
                    )
                else:
                    selectors = GENERIC_SELECTORS
                results.append(
                    IdentifiedInteraction(
                        url=base_url,
                        widget_type="generic",
                        selectors=selectors,
                        confidence=0.5,
                        frame=None,
                    )
                )
                break
            except Exception:
                continue
    except Exception:
        pass
    return results


def run_identify(url: str | None = None, urls: list[str] | None = None) -> list[IdentifiedInteraction]:
    """
    Load page(s) and detect AI chat widgets. Returns list of IdentifiedInteraction per URL.
    Call with either url= or urls= (list).
    """
    if url is not None:
        urls_to_use = [url]
    elif urls:
        urls_to_use = urls
    else:
        return []

    all_results: list[IdentifiedInteraction] = []

    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            try:
                for u in urls_to_use:
                    parsed = urlparse(u)
                    if not parsed.scheme:
                        u = "https://" + u
                    page = browser.new_page()
                    try:
                        page.goto(u, wait_until="domcontentloaded", timeout=20000)
                        base_url = page.url
                        # Known signatures first
                        found = _detect_by_signatures(page, base_url)
                        if not found:
                            found = _detect_by_heuristics(page, base_url)
                        all_results.extend(found)
                    finally:
                        page.close()
            finally:
                browser.close()
    except Exception:
        pass

    return all_results
