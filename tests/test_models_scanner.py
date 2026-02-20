"""Tests for jackai.models.scanner."""

import pytest
from pydantic import ValidationError

from jackai.models.config import WebWidgetSelectors
from jackai.models.scanner import (
    ContextWipeTestResult,
    IdentifiedInteraction,
    ScrapeInput,
    ScrapeResult,
)
from jackai.models.config import TargetConfig


@pytest.fixture
def selectors() -> WebWidgetSelectors:
    return WebWidgetSelectors(
        input_selector="#i",
        message_list_selector=".m",
    )


class TestScrapeInput:
    def test_seeds_required(self) -> None:
        # Pydantic allows empty list unless we add a validator; seeds=[] is valid
        i = ScrapeInput(seeds=[])
        assert i.seeds == []
        i = ScrapeInput(seeds=["https://a.com"])
        assert i.seeds == ["https://a.com"]
        assert i.crawl_depth == 0
        assert i.use_sitemap is False

    def test_crawl_depth_ge_zero(self) -> None:
        i = ScrapeInput(seeds=["x"], crawl_depth=2)
        assert i.crawl_depth == 2
        with pytest.raises(ValidationError):
            ScrapeInput(seeds=["x"], crawl_depth=-1)

    def test_use_sitemap(self) -> None:
        i = ScrapeInput(seeds=["x"], use_sitemap=True)
        assert i.use_sitemap is True


class TestScrapeResult:
    def test_default_empty(self) -> None:
        r = ScrapeResult()
        assert r.urls == []

    def test_urls_list(self) -> None:
        r = ScrapeResult(urls=["https://a.com", "https://b.com"])
        assert len(r.urls) == 2


class TestIdentifiedInteraction:
    def test_required_fields(self, selectors: WebWidgetSelectors) -> None:
        i = IdentifiedInteraction(
            url="https://x.com",
            widget_type="generic",
            selectors=selectors,
        )
        assert i.url == "https://x.com"
        assert i.widget_type == "generic"
        assert i.confidence == 0.0  # default
        assert i.frame is None

    def test_confidence_bounds(self, selectors: WebWidgetSelectors) -> None:
        i = IdentifiedInteraction(
            url="https://x.com",
            widget_type="g",
            selectors=selectors,
            confidence=0.9,
        )
        assert i.confidence == 0.9
        with pytest.raises(ValidationError):
            IdentifiedInteraction(
                url="x",
                widget_type="g",
                selectors=selectors,
                confidence=1.5,
            )
        with pytest.raises(ValidationError):
            IdentifiedInteraction(
                url="x",
                widget_type="g",
                selectors=selectors,
                confidence=-0.1,
            )


class TestContextWipeTestResult:
    def test_roundtrip(
        self,
        selectors: WebWidgetSelectors,
        identified_interaction: IdentifiedInteraction,
    ) -> None:
        target = TargetConfig(
            name="d",
            adapter_type="web_widget",
            url=identified_interaction.url,
            selectors=selectors,
            recommended_context_strategy="new_session",
        )
        r = ContextWipeTestResult(
            identified=identified_interaction,
            success=True,
            strategy_used="new_session",
            target_config=target,
        )
        assert r.success is True
        assert r.strategy_used == "new_session"
        assert r.target_config.name == "d"
        data = r.model_dump(mode="json")
        r2 = ContextWipeTestResult.model_validate(data)
        assert r2.success == r.success
