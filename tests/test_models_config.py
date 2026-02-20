"""Tests for jackai.models.config."""

import pytest
from pydantic import ValidationError

from jackai.models.config import TargetConfig, WebWidgetSelectors, WebWidgetTargetConfig


class TestWebWidgetSelectors:
    def test_required_fields(self) -> None:
        s = WebWidgetSelectors(
            input_selector="#input",
            message_list_selector=".messages",
        )
        assert s.input_selector == "#input"
        assert s.message_list_selector == ".messages"
        assert s.send_selector is None
        assert s.iframe_selector is None

    def test_all_fields(self) -> None:
        s = WebWidgetSelectors(
            input_selector="#input",
            message_list_selector=".messages",
            send_selector="button.send",
            widget_container_selector="#widget",
            iframe_selector="iframe#chat",
        )
        assert s.send_selector == "button.send"
        assert s.iframe_selector == "iframe#chat"

    def test_missing_required_raises(self) -> None:
        with pytest.raises(ValidationError):
            WebWidgetSelectors(message_list_selector=".m")  # type: ignore
        with pytest.raises(ValidationError):
            WebWidgetSelectors(input_selector="#i")  # type: ignore


class TestWebWidgetTargetConfig:
    def test_default_strategy(self, web_widget_selectors: WebWidgetSelectors) -> None:
        c = WebWidgetTargetConfig(url="https://x.com", selectors=web_widget_selectors)
        assert c.recommended_context_strategy == "new_session"

    def test_roundtrip_json(self, web_widget_selectors: WebWidgetSelectors) -> None:
        c = WebWidgetTargetConfig(
            url="https://x.com",
            selectors=web_widget_selectors,
            recommended_context_strategy="inject",
        )
        data = c.model_dump(mode="json")
        c2 = WebWidgetTargetConfig.model_validate(data)
        assert c2.url == c.url
        assert c2.recommended_context_strategy == "inject"


class TestTargetConfig:
    def test_web_widget_minimal(self, web_widget_selectors: WebWidgetSelectors) -> None:
        c = TargetConfig(
            name="t",
            adapter_type="web_widget",
            url="https://x.com",
            selectors=web_widget_selectors,
        )
        assert c.name == "t"
        assert c.adapter_type == "web_widget"
        assert c.url == "https://x.com"
        assert c.recommended_context_strategy == "new_session"

    def test_defaults(self) -> None:
        c = TargetConfig(name="t", adapter_type="telegram")
        assert c.url is None
        assert c.selectors is None
        assert c.widget_type is None
        assert c.extra is None

    def test_adapter_types(self) -> None:
        for adapter_type in ("web_widget", "telegram", "phone", "social"):
            c = TargetConfig(name="t", adapter_type=adapter_type)
            assert c.adapter_type == adapter_type

    def test_strategy_values(self, web_widget_selectors: WebWidgetSelectors) -> None:
        for strategy in ("new_session", "inject", "api"):
            c = TargetConfig(
                name="t",
                adapter_type="web_widget",
                url="https://x.com",
                selectors=web_widget_selectors,
                recommended_context_strategy=strategy,
            )
            assert c.recommended_context_strategy == strategy
