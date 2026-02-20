"""Interface contract models (send, receive, context)."""

from typing import Literal

from pydantic import BaseModel, Field


class Message(BaseModel):
    """A single message in a conversation."""

    role: Literal["user", "assistant"]
    content: str


class SendRequest(BaseModel):
    """Request to send a message through a channel."""

    content: str


class Reply(BaseModel):
    """Response from a channel (assistant reply)."""

    content: str
    channel_id: str | None = None


class ContextStrategy(BaseModel):
    """Strategy for clearing/overwriting context."""

    strategy: Literal["new_session", "inject", "api"] = "new_session"
    payload: str | None = Field(
        default=None,
        description="Optional injection payload when strategy is 'inject'"
    )


class ChatRequest(BaseModel):
    """Request to send a message to one or more channels."""

    channel_ids: list[str] = Field(..., description="Target channel ids (target names)")
    message: str = Field(..., description="Message content")


class ChatResponse(BaseModel):
    """Response from chat: replies per channel."""

    replies: list[Reply] = Field(default_factory=list)


class SetContextRequest(BaseModel):
    """Request to set context via injection payload."""

    payload: str = Field(..., description="Injection payload")


class ChannelStatus(BaseModel):
    """Channel/target with connection status for API."""

    id: str = Field(..., description="Target name / channel id")
    status: Literal["connected", "disconnected"] = "disconnected"
    adapter_type: str = "web_widget"
    widget_type: str | None = None
    url: str | None = None
