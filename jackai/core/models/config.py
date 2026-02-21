"""Target and adapter config models."""

from typing import Literal

from pydantic import BaseModel, Field


class WebWidgetSelectors(BaseModel):
    """Selectors for web widget DOM elements (input, messages, send)."""

    input_selector: str = Field(..., description="CSS selector for chat input")
    message_list_selector: str = Field(
        ..., description="CSS selector for message list/container"
    )
    send_selector: str | None = Field(
        default=None,
        description="CSS selector for send button (optional, Enter may submit)",
    )
    widget_container_selector: str | None = Field(
        default=None,
        description="Selector for widget root (e.g. to open/expand)",
    )
    iframe_selector: str | None = Field(
        default=None,
        description="If widget is in iframe, selector for that iframe"
    )


class WebWidgetTargetConfig(BaseModel):
    """Web widget target config (url + selectors)."""

    url: str
    selectors: WebWidgetSelectors
    recommended_context_strategy: Literal["new_session", "inject", "api"] = "new_session"


class TargetConfig(BaseModel):
    """Unified target config for any channel (used by session manager)."""

    name: str = Field(..., description="Display name / id for this target")
    adapter_type: Literal["web_widget", "telegram", "phone", "social"] = "web_widget"
    url: str | None = Field(default=None, description="URL for web_widget")
    selectors: WebWidgetSelectors | None = Field(
        default=None,
        description="Selectors for web_widget"
    )
    recommended_context_strategy: Literal["new_session", "inject", "api"] = "new_session"
    widget_type: str | None = Field(
        default=None,
        description="Provider name e.g. intercom, generic (for display)"
    )
    # Placeholder for other adapter configs (telegram token, etc.)
    extra: dict | None = None
