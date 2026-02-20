"""Tests for jackai.scanner.identify."""

from unittest.mock import MagicMock, patch

import pytest

from jackai.models.config import WebWidgetSelectors
from jackai.models.scanner import IdentifiedInteraction
from jackai.scanner.identify import run_identify


class TestRunIdentify:
    def test_empty_url_returns_empty(self) -> None:
        result = run_identify(url="")
        assert result == []

    def test_urls_none_returns_empty(self) -> None:
        result = run_identify(urls=[])
        assert result == []

    def test_single_url_returns_list(self) -> None:
        # Without mock this may hit the network and open browser
        result = run_identify(url="https://example.com")
        assert isinstance(result, list)
        # example.com may or may not have a chat widget
        assert all(isinstance(i, IdentifiedInteraction) for i in result)

    def test_multiple_urls_returns_flat_list(self) -> None:
        result = run_identify(urls=["https://example.com", "https://example.org"])
        assert isinstance(result, list)
        assert all(isinstance(i, IdentifiedInteraction) for i in result)


class TestIdentifiedInteractionShape:
    def test_identified_has_required_fields(self) -> None:
        sel = WebWidgetSelectors(
            input_selector="#i",
            message_list_selector=".m",
        )
        i = IdentifiedInteraction(
            url="https://x.com",
            widget_type="generic",
            selectors=sel,
            confidence=0.5,
        )
        assert i.url == "https://x.com"
        assert i.widget_type == "generic"
        assert i.selectors.input_selector == "#i"
        assert i.confidence == 0.5
        assert i.frame is None
