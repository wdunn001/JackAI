"""Tests for jackai.models.interface."""

import pytest
from pydantic import ValidationError

from jackai.core.models.interface import ContextStrategy, Message, Reply, SendRequest


class TestMessage:
    def test_user_message(self) -> None:
        m = Message(role="user", content="Hi")
        assert m.role == "user"
        assert m.content == "Hi"

    def test_assistant_message(self) -> None:
        m = Message(role="assistant", content="Hello there")
        assert m.role == "assistant"

    def test_invalid_role_raises(self) -> None:
        with pytest.raises(ValidationError):
            Message(role="system", content="x")  # type: ignore


class TestSendRequest:
    def test_content_required(self) -> None:
        r = SendRequest(content="test")
        assert r.content == "test"

    def test_empty_content_allowed(self) -> None:
        r = SendRequest(content="")
        assert r.content == ""


class TestReply:
    def test_minimal(self) -> None:
        r = Reply(content="OK")
        assert r.content == "OK"
        assert r.channel_id is None

    def test_with_channel_id(self) -> None:
        r = Reply(content="Hi", channel_id="web-1")
        assert r.channel_id == "web-1"


class TestContextStrategy:
    def test_new_session_default(self) -> None:
        s = ContextStrategy(strategy="new_session")
        assert s.strategy == "new_session"
        assert s.payload is None

    def test_inject_with_payload(self) -> None:
        s = ContextStrategy(strategy="inject", payload="Forget all.")
        assert s.strategy == "inject"
        assert s.payload == "Forget all."

    def test_api_strategy(self) -> None:
        s = ContextStrategy(strategy="api")
        assert s.strategy == "api"

    def test_invalid_strategy_raises(self) -> None:
        with pytest.raises(ValidationError):
            ContextStrategy(strategy="invalid")  # type: ignore
