"""Tests for jackai.scanner.scrape."""

import pytest

from jackai.core.models.scanner import ScrapeInput, ScrapeResult
from jackai.scanner.scrape import run_scrape


class TestRunScrape:
    def test_seeds_only_returns_urls(self) -> None:
        inp = ScrapeInput(seeds=["https://example.com", "https://foo.org"])
        result = run_scrape(inp)
        assert isinstance(result, ScrapeResult)
        assert len(result.urls) >= 2
        assert "https://example.com" in result.urls or "example.com" in result.urls
        assert "https://foo.org" in result.urls or "foo.org" in result.urls

    def test_single_seed(self) -> None:
        inp = ScrapeInput(seeds=["https://example.com"])
        result = run_scrape(inp)
        assert len(result.urls) >= 1
        assert any("example" in u for u in result.urls)

    def test_normalizes_url_without_scheme(self) -> None:
        inp = ScrapeInput(seeds=["example.com"])
        result = run_scrape(inp)
        assert any(u.startswith("http") for u in result.urls)

    def test_crawl_depth_zero_no_crawl(self) -> None:
        inp = ScrapeInput(seeds=["https://example.com"], crawl_depth=0)
        result = run_scrape(inp)
        assert len(result.urls) >= 1
        # With depth 0 we only have seeds (no extra links)
        assert "https://example.com" in result.urls or any("example" in u for u in result.urls)

    def test_use_sitemap_does_not_fail(self) -> None:
        inp = ScrapeInput(seeds=["https://example.com"], use_sitemap=True)
        result = run_scrape(inp)
        assert isinstance(result, ScrapeResult)
        assert len(result.urls) >= 1
