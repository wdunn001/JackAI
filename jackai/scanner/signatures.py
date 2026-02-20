"""Known widget signatures: provider name, selectors, optional iframe."""

from pydantic import BaseModel, Field

from jackai.models.config import WebWidgetSelectors


class WidgetSignature(BaseModel):
    """Signature for a known chat widget (provider + selectors)."""

    provider: str = Field(..., description="e.g. intercom, zendesk, generic")
    selectors: WebWidgetSelectors
    script_selector: str | None = Field(
        default=None,
        description="e.g. script[src*='intercom'] to detect presence"
    )
    iframe_selector: str | None = Field(default=None)
    container_selector: str | None = Field(
        default=None,
        description="Selector for widget root (to open/expand)"
    )


# Registry of known widget signatures (DOM/script patterns)
KNOWN_WIDGET_SIGNATURES: list[WidgetSignature] = [
    WidgetSignature(
        provider="intercom",
        selectors=WebWidgetSelectors(
            input_selector="[contenteditable='true']",
            message_list_selector=".intercom-messenger-body, [class*='messenger']",
            send_selector="button[aria-label*='Send'], [class*='send-button']",
            iframe_selector="iframe#intercom-frame, iframe[title*='Intercom']",
        ),
        script_selector="script[src*='intercom']",
        iframe_selector="iframe#intercom-frame, iframe[title*='Intercom']",
    ),
    WidgetSignature(
        provider="zendesk",
        selectors=WebWidgetSelectors(
            input_selector="textarea[placeholder*='Message'], #request_comment",
            message_list_selector=".chat-log, .messenger-conversation, [class*='conversation']",
            send_selector="button[type='submit'], [data-testid='send']",
            iframe_selector="iframe#launcher, iframe[title*='Zendesk']",
        ),
        script_selector="script[src*='zendesk']",
        iframe_selector="iframe#launcher, iframe[title*='Zendesk']",
    ),
    WidgetSignature(
        provider="drift",
        selectors=WebWidgetSelectors(
            input_selector="#drift-widget input[type='text'], [contenteditable='true']",
            message_list_selector="#drift-widget .conversation, [class*='conversation']",
            send_selector="#drift-widget button[type='submit'], [class*='send']",
            widget_container_selector="#drift-widget",
        ),
        script_selector="script[src*='drift']",
    ),
    WidgetSignature(
        provider="tawk",
        selectors=WebWidgetSelectors(
            input_selector="textarea#tawk-message-input, [contenteditable='true']",
            message_list_selector=".tawk-minified-container .chat-content, [class*='chat-content']",
            send_selector="button[title*='Send'], .tawk-send",
            iframe_selector="iframe#tawk-iframe",
        ),
        script_selector="script[src*='tawk']",
        iframe_selector="iframe#tawk-iframe",
    ),
    WidgetSignature(
        provider="crisp",
        selectors=WebWidgetSelectors(
            input_selector="[contenteditable='true'], input[placeholder*='message']",
            message_list_selector=".cc-window .cc-messages, [class*='messages']",
            send_selector="button[type='submit'], [class*='send']",
            iframe_selector="iframe[src*='crisp']",
        ),
        script_selector="script[src*='crisp']",
        iframe_selector="iframe[src*='crisp']",
    ),
    WidgetSignature(
        provider="hubspot",
        selectors=WebWidgetSelectors(
            input_selector="textarea, [contenteditable='true']",
            message_list_selector=".conversation-inner, [class*='conversation']",
            send_selector="button[type='submit'], [aria-label*='Send']",
            iframe_selector="iframe[id*='hubspot']",
        ),
        script_selector="script[src*='hubspot']",
        iframe_selector="iframe[id*='hubspot']",
    ),
]


def get_signatures() -> list[WidgetSignature]:
    """Return the list of known widget signatures (can be extended from file)."""
    return list(KNOWN_WIDGET_SIGNATURES)
