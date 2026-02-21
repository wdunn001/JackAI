"""Channel session registry: multiple channels by id (target name)."""

from typing import Any

from jackai.core.adapters.base import ChannelAdapterBase
from jackai.core.adapters.web_widget import WebWidgetAdapter
from jackai.core.models.config import TargetConfig
from jackai.core.models.interface import ContextStrategy, Reply, SendRequest
from jackai.core.session import SessionManager


def _adapter_for_config(config: TargetConfig) -> ChannelAdapterBase:
    """Return the appropriate adapter instance for the target config."""
    if config.adapter_type == "web_widget":
        return WebWidgetAdapter()
    # Stub for others
    from jackai.core.adapters.telegram import TelegramAdapter
    if config.adapter_type == "telegram":
        return TelegramAdapter()
    raise ValueError(f"Unsupported adapter_type: {config.adapter_type!r}")


class ChannelRegistry:
    """Holds multiple channel sessions keyed by target name (id)."""

    def __init__(self) -> None:
        self._sessions: dict[str, tuple[SessionManager, TargetConfig]] = {}

    def connect(self, channel_id: str, config: TargetConfig) -> None:
        """Connect a channel by id using the given config."""
        self.disconnect(channel_id)
        adapter = _adapter_for_config(config)
        sm = SessionManager()
        sm.connect(adapter, config)
        self._sessions[channel_id] = (sm, config)

    def disconnect(self, channel_id: str) -> None:
        """Disconnect a channel by id."""
        if channel_id in self._sessions:
            sm, _ = self._sessions[channel_id]
            sm.disconnect()
            del self._sessions[channel_id]

    def send(self, channel_id: str, request: SendRequest) -> Reply:
        """Send a message on a channel; raise if not connected."""
        if channel_id not in self._sessions:
            raise RuntimeError(f"Channel {channel_id!r} not connected")
        sm, config = self._sessions[channel_id]
        reply = sm.send(request)
        reply.channel_id = channel_id
        return reply

    def clear_context(self, channel_id: str, strategy: ContextStrategy) -> None:
        if channel_id not in self._sessions:
            raise RuntimeError(f"Channel {channel_id!r} not connected")
        self._sessions[channel_id][0].clear_context(strategy)

    def set_context(self, channel_id: str, payload: str) -> None:
        if channel_id not in self._sessions:
            raise RuntimeError(f"Channel {channel_id!r} not connected")
        self._sessions[channel_id][0].set_context(payload)

    def is_connected(self, channel_id: str) -> bool:
        if channel_id not in self._sessions:
            return False
        return self._sessions[channel_id][0].is_connected()

    def connected_ids(self) -> set[str]:
        return {cid for cid in self._sessions if self._sessions[cid][0].is_connected()}

    def get_config(self, channel_id: str) -> TargetConfig | None:
        if channel_id not in self._sessions:
            return None
        return self._sessions[channel_id][1]


# Global registry for the API (single-user PoC)
_registry: ChannelRegistry | None = None


def get_registry() -> ChannelRegistry:
    global _registry
    if _registry is None:
        _registry = ChannelRegistry()
    return _registry
