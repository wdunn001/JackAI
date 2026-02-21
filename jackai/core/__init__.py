"""JackAI core: models, adapters, session, context, config."""

from jackai.core.config_loader import get_targets_dir, load_targets
from jackai.core.context import get_injection_payloads
from jackai.core.models import (
    TargetConfig,
    WebWidgetSelectors,
    WebWidgetTargetConfig,
    ContextStrategy,
    Message,
    Reply,
    SendRequest,
    ScrapeInput,
    ScrapeResult,
    IdentifiedInteraction,
    ContextWipeTestResult,
)
from jackai.core.session import SessionManager

__all__ = [
    "get_targets_dir",
    "load_targets",
    "get_injection_payloads",
    "TargetConfig",
    "WebWidgetSelectors",
    "WebWidgetTargetConfig",
    "ContextStrategy",
    "Message",
    "Reply",
    "SendRequest",
    "ScrapeInput",
    "ScrapeResult",
    "IdentifiedInteraction",
    "ContextWipeTestResult",
    "SessionManager",
]
