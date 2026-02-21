"""Tests for jackai.scanner.test_context_wipe (with mocked adapter)."""

from unittest.mock import MagicMock, patch

import pytest

from jackai.core.models.config import TargetConfig, WebWidgetSelectors
from jackai.core.models.interface import Reply, SendRequest
from jackai.core.models.scanner import ContextWipeTestResult, IdentifiedInteraction
from jackai.scanner.test_context_wipe import (
    CONTEXT_SET_MESSAGE,
    PROBE_MESSAGE,
    SECRET_REVEAL_INDICATOR,
    run_context_wipe_test,
)


@pytest.fixture
def identified_for_wipe(web_widget_selectors: WebWidgetSelectors) -> IdentifiedInteraction:
    return IdentifiedInteraction(
        url="https://example.com",
        widget_type="generic",
        selectors=web_widget_selectors,
        confidence=0.8,
        frame=None,
    )


class TestContextWipeConstants:
    def test_context_set_message_contains_secret(self) -> None:
        assert "BANANA" in CONTEXT_SET_MESSAGE

    def test_probe_message_asks_for_secret(self) -> None:
        assert "secret" in PROBE_MESSAGE.lower() or "word" in PROBE_MESSAGE.lower()

    def test_secret_reveal_indicator(self) -> None:
        assert SECRET_REVEAL_INDICATOR == "BANANA"


class TestRunContextWipeTest:
    def test_returns_context_wipe_test_result(
        self,
        identified_for_wipe: IdentifiedInteraction,
    ) -> None:
        # Mock WebWidgetAdapter so we don't launch browser
        mock_adapter = MagicMock()
        mock_adapter.send.return_value = Reply(content="I don't know.", channel_id=None)
        mock_adapter.is_connected.return_value = True

        with patch("jackai.scanner.test_context_wipe.WebWidgetAdapter", return_value=mock_adapter):
            result = run_context_wipe_test(identified_for_wipe)
        assert isinstance(result, ContextWipeTestResult)
        assert result.identified == identified_for_wipe
        assert result.target_config.adapter_type == "web_widget"
        assert result.target_config.url == identified_for_wipe.url

    def test_connect_failure_returns_failure_result(
        self,
        identified_for_wipe: IdentifiedInteraction,
    ) -> None:
        with patch("jackai.scanner.test_context_wipe.WebWidgetAdapter") as MockAdapter:
            MockAdapter.return_value.connect.side_effect = RuntimeError("No browser")
            result = run_context_wipe_test(identified_for_wipe)
        assert result.success is False
        assert result.strategy_used == ""
        assert result.target_config.name

    def test_result_contains_target_config(
        self,
        identified_for_wipe: IdentifiedInteraction,
    ) -> None:
        mock_adapter = MagicMock()
        mock_adapter.send.return_value = Reply(content="Nope.", channel_id=None)
        mock_adapter.is_connected.return_value = True

        with patch("jackai.scanner.test_context_wipe.WebWidgetAdapter", return_value=mock_adapter):
            result = run_context_wipe_test(identified_for_wipe)
        assert result.target_config is not None
        assert result.target_config.selectors == identified_for_wipe.selectors
