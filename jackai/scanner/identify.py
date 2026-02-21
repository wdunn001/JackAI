"""Identify: load page, detect chat widgets via signatures and heuristics, return IdentifiedInteraction[]."""

import logging
from urllib.parse import urlparse

from jackai.core.models.config import WebWidgetSelectors
from jackai.core.models.scanner import IdentifiedInteraction
from jackai.scanner.signatures import get_signatures

logger = logging.getLogger(__name__)

# Wait this long after page load so JS-injected widgets can appear (ms)
WIDGET_LOAD_WAIT_MS = 10000

# Generic heuristics: selectors for unknown chat-like widgets (broad placeholders for "Ask", "Help", etc.)
GENERIC_SELECTORS = WebWidgetSelectors(
    input_selector=(
        "[contenteditable='true'], "
        "[id*='inputField' i], [id*='CXUI_input' i], "
        "textarea[placeholder*='message' i], textarea[placeholder*='Type' i], textarea[placeholder*='Ask' i], "
        "textarea[placeholder*='help' i], textarea[placeholder*='Write' i], textarea[placeholder*='Say' i], "
        "input[type='text'][placeholder*='message' i], input[placeholder*='message' i], "
        "input[placeholder*='Ask' i], input[placeholder*='Type' i], input[placeholder*='help' i]"
    ),
    message_list_selector="[id*='CXUI_container' i], [id*='CXUI' i], [class*='message'][class*='list'], [class*='chat'][class*='content'], [class*='conversation'], .messages, .chat-messages, [class*='message'], [class*='bubble'], [class*='thread'], [role='log']",
    send_selector="button[type='submit'], button[class*='send' i], [aria-label*='send' i], [aria-label*='Send' i]",
    widget_container_selector="[id*='CXUI' i], [id*='genesys' i], [class*='chat'][class*='widget' i], [id*='chat' i], [class*='messenger'], [class*='support'], [class*='conversation'], [class*='intercom'], [class*='launcher']",
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


def _heuristic_in_context(ctx, base_url: str, frame_selector: str | None) -> list[IdentifiedInteraction]:
    """Run heuristic detection in a page or frame context. Returns list of 0 or 1 result."""
    results: list[IdentifiedInteraction] = []
    try:
        container_sel = (
            "[id*='CXUI' i], [id*='genesys' i], "
            "[class*='chat' i], [id*='chat' i], [class*='messenger' i], [class*='widget' i], "
            "[class*='support' i], [class*='conversation' i], [id*='widget' i], "
            "[class*='intercom' i], [class*='launcher' i], [class*='bubble' i], [class*='thread' i]"
        )
        candidates = ctx.locator(container_sel).all()
        for el in candidates:
            try:
                inp = el.locator(GENERIC_SELECTORS.input_selector).first
                if inp.count() == 0:
                    continue
                msg_list = el.locator(GENERIC_SELECTORS.message_list_selector).first
                if msg_list.count() == 0:
                    msg_sel = el.locator("[class*='message' i], [class*='bubble' i], .msg, li, p, [role='log']").first
                    if msg_sel.count() == 0:
                        # Input-only: accept widget with chat-like input in widget container (empty thread)
                        selectors = WebWidgetSelectors(
                            input_selector=GENERIC_SELECTORS.input_selector,
                            message_list_selector="[class*='message' i], [class*='bubble' i], .msg, li, p, [role='log'], [class*='conversation']",
                            send_selector=GENERIC_SELECTORS.send_selector,
                            widget_container_selector=GENERIC_SELECTORS.widget_container_selector,
                        )
                        results.append(
                            IdentifiedInteraction(
                                url=base_url,
                                widget_type="generic",
                                selectors=selectors,
                                confidence=0.35,
                                frame=frame_selector,
                            )
                        )
                        return results
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
                        frame=frame_selector,
                    )
                )
                return results
            except Exception:
                continue
        # No container matched: try page/frame-level (input + message area anywhere, or input-only)
        inp = ctx.locator(GENERIC_SELECTORS.input_selector).first
        if inp.count() > 0:
            msg = ctx.locator(GENERIC_SELECTORS.message_list_selector).first
            if msg.count() == 0:
                msg = ctx.locator("[class*='message' i], [class*='bubble' i], .msg, li, p, [role='log']").first
            if msg.count() > 0:
                results.append(
                    IdentifiedInteraction(
                        url=base_url,
                        widget_type="generic",
                        selectors=GENERIC_SELECTORS,
                        confidence=0.4,
                        frame=frame_selector,
                    )
                )
            else:
                # Single chat-like input on page/frame (e.g. minimal widget)
                results.append(
                    IdentifiedInteraction(
                        url=base_url,
                        widget_type="generic",
                        selectors=GENERIC_SELECTORS,
                        confidence=0.3,
                        frame=frame_selector,
                    )
                )
    except Exception as e:
        logger.debug("heuristic_in_context failed: %s", e)
    return results


def _detect_by_heuristics(page, base_url: str) -> list[IdentifiedInteraction]:
    """Detect chat-like containers by heuristics. Checks main page then each iframe."""
    results: list[IdentifiedInteraction] = []
    try:
        results = _heuristic_in_context(page, base_url, None)
        if results:
            return results
        for frame in page.frames:
            if frame == page.main_frame:
                continue
            try:
                frame_selector = "iframe"
                frame_el = frame.frame_element()
                fid = frame_el.get_attribute("id")
                fname = frame_el.get_attribute("name")
                if fid:
                    frame_selector = f"iframe#{fid}"
                elif fname:
                    frame_selector = f"iframe[name=\"{fname}\"]"
                results = _heuristic_in_context(frame, base_url, frame_selector)
                if results:
                    return results
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
                    logger.info("identify: loading %s", u)
                    page = browser.new_page()
                    try:
                        page.goto(u, wait_until="domcontentloaded", timeout=25000)
                        base_url = page.url
                        # Give JS-injected widgets time to render (many load after DOM ready)
                        page.wait_for_timeout(WIDGET_LOAD_WAIT_MS)
                        frame_count = len(page.frames)
                        logger.info("identify: %s frames after wait", frame_count)
                        # Known signatures first
                        found = _detect_by_signatures(page, base_url)
                        if found:
                            logger.info("identify: signature match(es): %s", [f.widget_type for f in found])
                        if not found:
                            found = _detect_by_heuristics(page, base_url)
                            if found:
                                logger.info("identify: heuristic match(es): %s", [f.widget_type for f in found])
                        all_results.extend(found)
                    finally:
                        page.close()
            finally:
                browser.close()
    except Exception as e:
        logger.exception("identify failed: %s", e)

    return all_results
