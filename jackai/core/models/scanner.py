"""Scanner pipeline models (scrape, identify, test context wipe)."""

from pydantic import BaseModel, Field

from jackai.core.models.config import TargetConfig, WebWidgetSelectors


class ScrapeInput(BaseModel):
    """Input for URL collection (seeds, optional crawl/sitemap)."""

    seeds: list[str] = Field(..., description="Seed URLs to start from")
    crawl_depth: int = Field(default=0, ge=0, description="Same-origin link depth (0 = no crawl)")
    use_sitemap: bool = Field(default=False, description="Try to fetch sitemap.xml for URLs")


class ScrapeResult(BaseModel):
    """Result of scrape: list of page URLs to analyze."""

    urls: list[str] = Field(default_factory=list)


class IdentifiedInteraction(BaseModel):
    """A detected AI chat / support widget on a page."""

    url: str
    widget_type: str = Field(..., description="e.g. intercom, zendesk, generic")
    selectors: WebWidgetSelectors
    confidence: float = Field(default=0.0, ge=0, le=1, description="Detection confidence 0-1")
    frame: str | None = Field(default=None, description="Iframe selector if widget is in iframe")


class ContextWipeTestResult(BaseModel):
    """Result of context-wipe test: success, strategy used, and target config."""

    identified: IdentifiedInteraction
    success: bool
    strategy_used: str = Field(..., description="new_session or inject")
    target_config: TargetConfig
