"""Tests for jackai.session.SessionManager."""

import pytest

from jackai.models.config import TargetConfig
from jackai.models.interface import ContextStrategy, Reply, SendRequest
from jackai.session import SessionManager

from jackai.adapters.base import ChannelAdapterBase


class MockAdapter(ChannelAdapterBase):
    """Mock adapter for testing SessionManager."""

    def __init__(self) -> None:
        self._connected = False
        self._config: TargetConfig | None = None
        self.send_calls: list[str] = []
        self.clear_context_calls: list[ContextStrategy] = []
        self.set_context_calls: list[str] = []

    def connect(self, config: TargetConfig) -> None:
        self._config = config
        self._connected = True

    def send(self, request: SendRequest) -> Reply:
        self.send_calls.append(request.content)
        return Reply(content=f"reply:{request.content}", channel_id="mock")

    def clear_context(self, strategy: ContextStrategy) -> None:
        self.clear_context_calls.append(strategy)

    def set_context(self, payload: str) -> None:
        self.set_context_calls.append(payload)

    def disconnect(self) -> None:
        self._connected = False
        self._config = None

    def is_connected(self) -> bool:
        return self._connected


class TestSessionManager:
    def test_init_not_connected(self) -> None:
        sm = SessionManager()
        assert sm.is_connected() is False
        assert sm.adapter is None
        assert sm.config is None

    def test_connect_sets_adapter_and_config(
        self,
        target_config: TargetConfig,
    ) -> None:
        sm = SessionManager()
        adapter = MockAdapter()
        sm.connect(adapter, target_config)
        assert sm.adapter is adapter
        assert sm.config == target_config
        assert sm.is_connected() is True
        assert adapter._connected is True

    def test_connect_disconnects_previous(
        self,
        target_config: TargetConfig,
    ) -> None:
        sm = SessionManager()
        a1 = MockAdapter()
        a2 = MockAdapter()
        sm.connect(a1, target_config)
        sm.connect(a2, target_config)
        assert sm.adapter is a2
        assert a1._connected is False
        assert a2._connected is True

    def test_send_when_connected(
        self,
        target_config: TargetConfig,
        send_request: SendRequest,
    ) -> None:
        sm = SessionManager()
        adapter = MockAdapter()
        sm.connect(adapter, target_config)
        reply = sm.send(send_request)
        assert reply.content == "reply:Hello"
        assert adapter.send_calls == ["Hello"]

    def test_send_when_not_connected_raises(self, send_request: SendRequest) -> None:
        sm = SessionManager()
        with pytest.raises(RuntimeError, match="Not connected"):
            sm.send(send_request)

    def test_clear_context_when_connected(
        self,
        target_config: TargetConfig,
        context_strategy_new_session: ContextStrategy,
    ) -> None:
        sm = SessionManager()
        adapter = MockAdapter()
        sm.connect(adapter, target_config)
        sm.clear_context(context_strategy_new_session)
        assert len(adapter.clear_context_calls) == 1
        assert adapter.clear_context_calls[0].strategy == "new_session"

    def test_clear_context_when_not_connected_raises(
        self,
        context_strategy_new_session: ContextStrategy,
    ) -> None:
        sm = SessionManager()
        with pytest.raises(RuntimeError, match="Not connected"):
            sm.clear_context(context_strategy_new_session)

    def test_set_context_when_connected(
        self,
        target_config: TargetConfig,
    ) -> None:
        sm = SessionManager()
        adapter = MockAdapter()
        sm.connect(adapter, target_config)
        sm.set_context("New instructions.")
        assert adapter.set_context_calls == ["New instructions."]

    def test_set_context_when_not_connected_raises(self) -> None:
        sm = SessionManager()
        with pytest.raises(RuntimeError, match="Not connected"):
            sm.set_context("x")

    def test_disconnect_clears_state(
        self,
        target_config: TargetConfig,
    ) -> None:
        sm = SessionManager()
        adapter = MockAdapter()
        sm.connect(adapter, target_config)
        sm.disconnect()
        assert sm.adapter is None
        assert sm.config is None
        assert sm.is_connected() is False
        assert adapter._connected is False

    def test_disconnect_idempotent(self, target_config: TargetConfig) -> None:
        sm = SessionManager()
        adapter = MockAdapter()
        sm.connect(adapter, target_config)
        sm.disconnect()
        sm.disconnect()
        assert sm.adapter is None
