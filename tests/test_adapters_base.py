"""Tests for jackai.adapters.base."""

import pytest

from jackai.core.adapters.base import ChannelAdapterBase
from jackai.core.adapters.telegram import TelegramAdapter
from jackai.core.models.config import TargetConfig
from jackai.core.models.interface import ContextStrategy, Reply, SendRequest


class TestChannelAdapterBase:
    def test_telegram_adapter_is_subclass(self) -> None:
        assert issubclass(TelegramAdapter, ChannelAdapterBase)


class TestTelegramAdapter:
    def test_connect_raises_not_implemented(self) -> None:
        adapter = TelegramAdapter()
        config = TargetConfig(name="t", adapter_type="telegram")
        with pytest.raises(NotImplementedError):
            adapter.connect(config)

    def test_send_raises_not_implemented(self) -> None:
        adapter = TelegramAdapter()
        with pytest.raises(NotImplementedError):
            adapter.send(SendRequest(content="hi"))

    def test_clear_context_raises_not_implemented(self) -> None:
        adapter = TelegramAdapter()
        with pytest.raises(NotImplementedError):
            adapter.clear_context(ContextStrategy(strategy="new_session"))

    def test_set_context_raises_not_implemented(self) -> None:
        adapter = TelegramAdapter()
        with pytest.raises(NotImplementedError):
            adapter.set_context("x")

    def test_disconnect_no_op(self) -> None:
        adapter = TelegramAdapter()
        adapter.disconnect()

    def test_is_connected_false(self) -> None:
        adapter = TelegramAdapter()
        assert adapter.is_connected() is False
