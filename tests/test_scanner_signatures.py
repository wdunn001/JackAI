"""Tests for jackai.scanner.signatures."""

import pytest

from jackai.core.models.config import WebWidgetSelectors
from jackai.scanner.signatures import (
    WidgetSignature,
    get_signatures,
    KNOWN_WIDGET_SIGNATURES,
)


class TestWidgetSignature:
    def test_required_fields(self) -> None:
        sel = WebWidgetSelectors(
            input_selector="#i",
            message_list_selector=".m",
        )
        s = WidgetSignature(provider="test", selectors=sel)
        assert s.provider == "test"
        assert s.selectors == sel
        assert s.script_selector is None
        assert s.iframe_selector is None

    def test_all_fields(self) -> None:
        sel = WebWidgetSelectors(
            input_selector="#i",
            message_list_selector=".m",
        )
        s = WidgetSignature(
            provider="intercom",
            selectors=sel,
            script_selector="script[src*='intercom']",
            iframe_selector="iframe#intercom",
        )
        assert s.script_selector == "script[src*='intercom']"
        assert s.iframe_selector == "iframe#intercom"


class TestKnownWidgetSignatures:
    def test_registry_not_empty(self) -> None:
        assert len(KNOWN_WIDGET_SIGNATURES) > 0

    def test_each_has_provider_and_selectors(self) -> None:
        for sig in KNOWN_WIDGET_SIGNATURES:
            assert sig.provider
            assert sig.selectors.input_selector
            assert sig.selectors.message_list_selector

    def test_known_providers_present(self) -> None:
        providers = {s.provider for s in KNOWN_WIDGET_SIGNATURES}
        assert "intercom" in providers or "generic" in providers or "zendesk" in providers


class TestGetSignatures:
    def test_returns_list(self) -> None:
        sigs = get_signatures()
        assert isinstance(sigs, list)
        assert len(sigs) == len(KNOWN_WIDGET_SIGNATURES)

    def test_returns_copy(self) -> None:
        s1 = get_signatures()
        s2 = get_signatures()
        assert s1 is not s2
        assert s1 == s2
