"""Telegram adapter (stub). Bot API or Telethon can be implemented here."""

from jackai.core.adapters.base import ChannelAdapterBase
from jackai.core.models.config import TargetConfig
from jackai.core.models.interface import ContextStrategy, Reply, SendRequest


class TelegramAdapter(ChannelAdapterBase):
    """Stub: Telegram Bot API adapter (send message, get updates)."""

    def connect(self, config: TargetConfig) -> None:
        raise NotImplementedError("Telegram adapter not implemented in this PoC")

    def send(self, request: SendRequest) -> Reply:
        raise NotImplementedError("Telegram adapter not implemented in this PoC")

    def clear_context(self, strategy: ContextStrategy) -> None:
        raise NotImplementedError("Telegram adapter not implemented in this PoC")

    def set_context(self, payload: str) -> None:
        raise NotImplementedError("Telegram adapter not implemented in this PoC")

    def disconnect(self) -> None:
        pass

    def is_connected(self) -> bool:
        return False
