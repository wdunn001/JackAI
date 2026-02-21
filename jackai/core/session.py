"""Session manager: holds active adapter and delegates to it."""

from __future__ import annotations

from typing import TYPE_CHECKING

from jackai.core.models.config import TargetConfig
from jackai.core.models.interface import ContextStrategy, Reply, SendRequest

if TYPE_CHECKING:
    from jackai.core.adapters.base import ChannelAdapterBase


class SessionManager:
    """Manages a single active channel session (one adapter at a time per manager)."""

    def __init__(self) -> None:
        self._adapter: ChannelAdapterBase | None = None
        self._config: TargetConfig | None = None

    @property
    def adapter(self) -> "ChannelAdapterBase | None":
        return self._adapter

    @property
    def config(self) -> TargetConfig | None:
        return self._config

    def connect(self, adapter: "ChannelAdapterBase", config: TargetConfig) -> None:
        """Connect using the given adapter and config."""
        if self._adapter is not None:
            self._adapter.disconnect()
        self._adapter = adapter
        self._config = config
        self._adapter.connect(config)

    def send(self, request: SendRequest) -> Reply:
        """Send a message through the active adapter."""
        if self._adapter is None:
            raise RuntimeError("Not connected; call connect() first")
        return self._adapter.send(request)

    def clear_context(self, strategy: ContextStrategy) -> None:
        """Clear context using the given strategy."""
        if self._adapter is None:
            raise RuntimeError("Not connected; call connect() first")
        self._adapter.clear_context(strategy)

    def set_context(self, payload: str) -> None:
        """Set context via injection payload."""
        if self._adapter is None:
            raise RuntimeError("Not connected; call connect() first")
        self._adapter.set_context(payload)

    def disconnect(self) -> None:
        """Disconnect the active adapter."""
        if self._adapter is not None:
            self._adapter.disconnect()
            self._adapter = None
            self._config = None

    def is_connected(self) -> bool:
        """Return whether there is an active connection."""
        return self._adapter is not None and self._adapter.is_connected()
