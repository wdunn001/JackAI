"""Pydantic models shared by core, adapters, API, and scanner."""

from jackai.core.models.config import (
    TargetConfig,
    WebWidgetSelectors,
    WebWidgetTargetConfig,
)
from jackai.core.models.interface import (
    ContextStrategy,
    Message,
    Reply,
    SendRequest,
    ChatRequest,
    ChatResponse,
    SetContextRequest,
    ChannelStatus,
)
from jackai.core.models.scanner import (
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
    "ChatRequest",
    "ChatResponse",
    "SetContextRequest",
    "ChannelStatus",
    "ScrapeInput",
    "ScrapeResult",
    "IdentifiedInteraction",
    "ContextWipeTestResult",
]
