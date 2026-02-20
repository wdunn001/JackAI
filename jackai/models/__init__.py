"""Pydantic models shared by core, adapters, API, and scanner."""

from jackai.models.config import (
    TargetConfig,
    WebWidgetSelectors,
    WebWidgetTargetConfig,
)
from jackai.models.interface import (
    ContextStrategy,
    Message,
    Reply,
    SendRequest,
)
from jackai.models.scanner import (
    ContextWipeTestResult,
    IdentifiedInteraction,
    ScrapeInput,
    ScrapeResult,
)

__all__ = [
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
]
