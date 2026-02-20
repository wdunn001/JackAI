"""Tests for jackai.context."""

import pytest

from jackai.context import (
    DEFAULT_INJECTION_PAYLOADS,
    get_default_strategy,
    get_injection_payloads,
)
from jackai.models.interface import ContextStrategy


class TestContextModule:
    def test_get_injection_payloads_returns_list(self) -> None:
        payloads = get_injection_payloads()
        assert isinstance(payloads, list)
        assert len(payloads) > 0
        assert all(isinstance(p, str) for p in payloads)

    def test_default_payloads_content(self) -> None:
        payloads = get_injection_payloads()
        assert any("ignore" in p.lower() or "forget" in p.lower() for p in payloads)

    def test_payloads_are_copies(self) -> None:
        p1 = get_injection_payloads()
        p2 = get_injection_payloads()
        assert p1 is not p2
        assert p1 == p2

    def test_get_default_strategy(self) -> None:
        s = get_default_strategy()
        assert isinstance(s, ContextStrategy)
        assert s.strategy == "new_session"
        assert s.payload is None

    def test_default_injection_payloads_constant(self) -> None:
        assert len(DEFAULT_INJECTION_PAYLOADS) >= 1
