"""FastAPI application: channels, chat, scan, targets."""

import logging
from dataclasses import asdict
from pathlib import Path

from fastapi import FastAPI, HTTPException

logger = logging.getLogger(__name__)
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from jackai.api.channels import get_registry
from jackai.core.config_loader import get_targets_dir, load_targets
from jackai.core.models import (
    TargetConfig,
    ChannelStatus,
    ChatRequest,
    ChatResponse,
    ContextStrategy,
    Reply,
    SendRequest,
    SetContextRequest,
    ContextWipeTestResult,
    IdentifiedInteraction,
    ScrapeInput,
    ScrapeResult,
)
from jackai.scanner.adapter_factory import build_target_config_from_result, save_target_config
from jackai.scanner.identify import run_identify
from jackai.scanner.preset_tests import get_preset_categories, run_preset_tests
from jackai.scanner.scrape import run_scrape
from jackai.scanner.test_context_wipe import run_context_wipe_test


def _targets_dir() -> Path:
    return get_targets_dir()


def _load_targets() -> list[TargetConfig]:
    return load_targets()


class IdentifyInput(BaseModel):
    """Either url or urls must be provided."""

    url: str | None = Field(None, description="Single page URL to analyze")
    urls: list[str] | None = Field(None, description="Multiple page URLs")


class ClearContextBody(BaseModel):
    """Body for clear-context endpoint."""

    strategy: str = Field("new_session", description="new_session | inject | api")
    payload: str | None = Field(None, description="Injection payload when strategy is inject")


class ScanFullInput(BaseModel):
    """Body for full scan pipeline."""

    seeds: list[str] | None = Field(None, description="Seed URLs (alias: urls)")
    urls: list[str] | None = Field(None, description="Seed URLs (alias: seeds)")
    scrape_options: dict | None = Field(None, description="Optional ScrapeInput options (crawl_depth, use_sitemap)")


class PresetTestsInput(BaseModel):
    """Body for preset security tests (run against an identified widget)."""

    identified: IdentifiedInteraction = Field(..., description="Identified widget from /api/scan/identify")
    categories: list[str] | None = Field(None, description="Category ids to run (omit = all)")


def create_app() -> FastAPI:
    app = FastAPI(
        title="JackAI API",
        description="PoC for context-hijacking of publicly exposed AIs (security research). "
        "Unified interface to connect to web widgets, Telegram, etc.; send messages, clear/set context; "
        "scanner pipeline: scrape, identify, test context wipe.",
        version="0.1.0",
        openapi_url="/openapi.json",
        docs_url="/docs",
        redoc_url="/redoc",
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # --- Targets ---
    @app.get("/api/targets", response_model=list[TargetConfig], tags=["Targets"])
    def get_targets():
        """List configured targets (from config/targets/)."""
        return _load_targets()

    # --- Channels (connect, disconnect, chat, clear-context, set-context) ---
    @app.get("/api/channels", response_model=list[ChannelStatus], tags=["Channels"])
    def get_channels():
        """List configured targets/channels with status (connected/disconnected)."""
        targets = _load_targets()
        registry = get_registry()
        result: list[ChannelStatus] = []
        for t in targets:
            status = "connected" if registry.is_connected(t.name) else "disconnected"
            result.append(
                ChannelStatus(
                    id=t.name,
                    status=status,
                    adapter_type=t.adapter_type,
                    widget_type=t.widget_type,
                    url=t.url,
                )
            )
        return result

    @app.post("/api/channels/{channel_id}/connect", tags=["Channels"])
    def channel_connect(channel_id: str):
        """Connect to a channel (id = target name from config)."""
        targets = _load_targets()
        config = next((t for t in targets if t.name == channel_id), None)
        if not config:
            raise HTTPException(404, f"Target {channel_id!r} not found in config")
        try:
            get_registry().connect(channel_id, config)
            return {"ok": True, "channel_id": channel_id}
        except Exception as e:
            raise HTTPException(500, str(e))

    @app.post("/api/channels/{channel_id}/disconnect", tags=["Channels"])
    def channel_disconnect(channel_id: str):
        """Disconnect a channel."""
        get_registry().disconnect(channel_id)
        return {"ok": True, "channel_id": channel_id}

    @app.post("/api/chat", response_model=ChatResponse, tags=["Channels"])
    def chat(body: ChatRequest):
        """Send message to selected channels; return replies per channel."""
        registry = get_registry()
        replies: list = []
        for cid in body.channel_ids:
            if not registry.is_connected(cid):
                continue
            try:
                reply = registry.send(cid, SendRequest(content=body.message))
                replies.append(reply)
            except Exception as e:
                replies.append(Reply(content=f"Error: {e}", channel_id=cid))
        return ChatResponse(replies=replies)

    @app.post("/api/channels/{channel_id}/clear-context", tags=["Channels"])
    def channel_clear_context(channel_id: str, body: ClearContextBody):
        """Clear context on a channel (body: strategy, optional payload)."""
        strategy = ContextStrategy(strategy=body.strategy, payload=body.payload)
        try:
            get_registry().clear_context(channel_id, strategy)
            return {"ok": True, "channel_id": channel_id}
        except RuntimeError as e:
            raise HTTPException(400, str(e))

    @app.post("/api/channels/{channel_id}/set-context", tags=["Channels"])
    def channel_set_context(channel_id: str, body: SetContextRequest):
        """Set context via injection payload."""
        try:
            get_registry().set_context(channel_id, body.payload)
            return {"ok": True, "channel_id": channel_id}
        except RuntimeError as e:
            raise HTTPException(400, str(e))

    # --- Scan ---
    @app.post("/api/scan/scrape", response_model=ScrapeResult, tags=["Scan"])
    def scan_scrape(body: ScrapeInput):
        """Scrape: collect URLs from seeds (optional crawl/sitemap)."""
        return run_scrape(body)

    @app.post("/api/scan/identify", response_model=list[IdentifiedInteraction], tags=["Scan"])
    def scan_identify(body: IdentifyInput):
        """Identify: detect chat widgets on page(s). Provide either url or urls."""
        if body.url is not None:
            logger.info("scan/identify: url=%s", body.url)
            result = run_identify(url=body.url)
            logger.info("scan/identify: found %s widget(s)", len(result))
            return result
        if body.urls:
            logger.info("scan/identify: urls=%s", body.urls)
            result = run_identify(urls=body.urls)
            logger.info("scan/identify: found %s widget(s)", len(result))
            return result
        raise HTTPException(400, "Provide 'url' or 'urls'")

    @app.post("/api/scan/test-wipe", response_model=ContextWipeTestResult, tags=["Scan"])
    def scan_test_wipe(body: IdentifiedInteraction):
        """Test context wipe for an identified interaction."""
        return run_context_wipe_test(body)

    @app.post("/api/scan/full", response_model=dict, tags=["Scan"])
    def scan_full(body: ScanFullInput):
        """
        Full pipeline: scrape (if multiple seeds) -> identify -> test-wipe per candidate.
        Returns: { \"results\": [...], \"target_configs\": [...] }
        """
        seeds = body.seeds or body.urls or []
        if not seeds:
            raise HTTPException(400, "Provide 'seeds' or 'urls'")
        scrape_options = body.scrape_options or {}
        input_data = ScrapeInput(seeds=seeds, **scrape_options)
        scrape_result = run_scrape(input_data)
        all_identified: list[IdentifiedInteraction] = []
        for u in scrape_result.urls:
            all_identified.extend(run_identify(url=u))
        results: list[ContextWipeTestResult] = []
        target_configs: list[TargetConfig] = []
        for ident in all_identified:
            res = run_context_wipe_test(ident)
            results.append(res)
            target_configs.append(res.target_config)
        return {"results": results, "target_configs": target_configs}

    @app.post("/api/scan/save-target", response_model=dict, tags=["Scan"])
    def scan_save_target(body: TargetConfig):
        """Save a target config to config/targets/; return updated targets list."""
        saved_id = save_target_config(body)
        return {"saved": saved_id, "targets": _load_targets()}

    @app.get("/api/scan/preset-categories", tags=["Scan"])
    def scan_preset_categories():
        """List preset security test categories (prompt injection, role manipulation, etc.)."""
        return get_preset_categories()

    @app.post("/api/scan/preset-tests", tags=["Scan"])
    def scan_preset_tests(body: PresetTestsInput):
        """Run preset security tests against an identified widget. Returns results per payload."""
        results = run_preset_tests(body.identified, category_ids=body.categories)
        return {"results": [asdict(r) for r in results]}

    return app
