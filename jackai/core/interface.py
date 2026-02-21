"""Unified interface: connect, send, receive, clear_context, set_context, disconnect."""

from typing import Protocol

from jackai.core.models.config import TargetConfig
from jackai.core.models.interface import ContextStrategy, Reply, SendRequest


class ChannelAdapter(Protocol):
    """Protocol for channel adapters (web widget, telegram, etc.)."""

    def connect(self, config: TargetConfig) -> None:
        """Connect to the channel using the given config."""
        ...

    def send(self, request: SendRequest) -> Reply:
        """Send a message; return the reply."""
        ...

    def clear_context(self, strategy: ContextStrategy) -> None:
        """Clear or overwrite context (new session, inject, or api)."""
        ...

    def set_context(self, payload: str) -> None:
        """Set context via injection payload (if supported)."""
        ...

    def disconnect(self) -> None:
        """Disconnect from the channel."""
        ...

    def is_connected(self) -> bool:
        """Return whether the adapter is currently connected."""
        ...
