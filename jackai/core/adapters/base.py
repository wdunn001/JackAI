"""Base adapter: abstract interface for all channel adapters."""

from abc import ABC, abstractmethod

from jackai.core.models.config import TargetConfig
from jackai.core.models.interface import ContextStrategy, Reply, SendRequest


class ChannelAdapterBase(ABC):
    """Abstract base for channel adapters (web widget, telegram, etc.)."""

    @abstractmethod
    def connect(self, config: TargetConfig) -> None:
        """Connect to the channel using the given config."""
        pass

    @abstractmethod
    def send(self, request: SendRequest) -> Reply:
        """Send a message; return the reply."""
        pass

    @abstractmethod
    def clear_context(self, strategy: ContextStrategy) -> None:
        """Clear or overwrite context (new session, inject, or api)."""
        pass

    @abstractmethod
    def set_context(self, payload: str) -> None:
        """Set context via injection payload (if supported)."""
        pass

    @abstractmethod
    def disconnect(self) -> None:
        """Disconnect from the channel."""
        pass

    @abstractmethod
    def is_connected(self) -> bool:
        """Return whether the adapter is currently connected."""
        pass
