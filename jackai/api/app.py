"""FastAPI application: channels, chat, scan, targets."""

from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from jackai.api.channels import get_registry
from jackai.config_loader import get_targets_dir, load_targets
from jackai.models.config import TargetConfig
from jackai.models.interface import (
    ChannelStatus,
    ChatRequest,
    ChatResponse,
    ContextStrategy,
    Reply,
    SendRequest,
    SetContextRequest,
)
from jackai.models.scanner import (
    ContextWipeTestResult,
    IdentifiedInteraction,
    ScrapeInput,
    ScrapeResult,
)
from jackai.scanner.adapter_factory import build_target_config_from_result, save_target_config
from jackai.scanner.identify import run_identify
from jackai.scanner.scrape import run_scrape
from jackai.scanner.test_context_wipe import run_context_wipe_test


def _targets_dir() -> Path:
    return get_targets_dir()


def _load_targets() -> list[TargetConfig]:
    return load_targets()


def create_app() -> FastAPI:
    app = FastAPI(title="JackAI API", description="PoC for context-hijacking of publicly exposed AIs")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # --- Targets ---
    @app.get("/api/targets", response_model=list[TargetConfig])
    def get_targets():
        """List configured targets (from config/targets/)."""
        return _load_targets()

    # --- Channels (connect, disconnect, chat, clear-context, set-context) ---
    @app.get("/api/channels", response_model=list[ChannelStatus])
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

    @app.post("/api/channels/{channel_id}/connect")
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

    @app.post("/api/channels/{channel_id}/disconnect")
    def channel_disconnect(channel_id: str):
        """Disconnect a channel."""
        get_registry().disconnect(channel_id)
        return {"ok": True, "channel_id": channel_id}

    @app.post("/api/chat", response_model=ChatResponse)
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

    @app.post("/api/channels/{channel_id}/clear-context")
    def channel_clear_context(channel_id: str, body: dict):
        """Clear context on a channel (body: strategy, optional payload)."""
        strategy = ContextStrategy(
            strategy=body.get("strategy", "new_session"),
            payload=body.get("payload"),
        )
        try:
            get_registry().clear_context(channel_id, strategy)
            return {"ok": True, "channel_id": channel_id}
        except RuntimeError as e:
            raise HTTPException(400, str(e))

    @app.post("/api/channels/{channel_id}/set-context")
    def channel_set_context(channel_id: str, body: SetContextRequest):
        """Set context via injection payload."""
        try:
            get_registry().set_context(channel_id, body.payload)
            return {"ok": True, "channel_id": channel_id}
        except RuntimeError as e:
            raise HTTPException(400, str(e))

    # --- Scan ---
    @app.post("/api/scan/scrape", response_model=ScrapeResult)
    def scan_scrape(body: ScrapeInput):
        """Scrape: collect URLs from seeds (optional crawl/sitemap)."""
        return run_scrape(body)

    @app.post("/api/scan/identify", response_model=list[IdentifiedInteraction])
    def scan_identify(body: dict):
        """Identify: detect chat widgets on page(s). Body: { \"url\": \"...\" } or { \"urls\": [\"...\"] }."""
        if "url" in body:
            return run_identify(url=body["url"])
        if "urls" in body:
            return run_identify(urls=body["urls"])
        raise HTTPException(400, "Provide 'url' or 'urls'")

    @app.post("/api/scan/test-wipe", response_model=ContextWipeTestResult)
    def scan_test_wipe(body: IdentifiedInteraction):
        """Test context wipe for an identified interaction."""
        return run_context_wipe_test(body)

    @app.post("/api/scan/full", response_model=dict)
    def scan_full(body: dict):
        """
        Full pipeline: scrape (if multiple seeds) -> identify -> test-wipe per candidate.
        Body: { \"seeds\": [\"url1\", \"url2\"], \"scrape_options\": {...} }
        Returns: { \"results\": [...], \"target_configs\": [...] }
        """
        seeds = body.get("seeds") or body.get("urls") or []
        if not seeds:
            raise HTTPException(400, "Provide 'seeds' or 'urls'")
        scrape_options = body.get("scrape_options") or {}
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

    @app.post("/api/scan/save-target", response_model=dict)
    def scan_save_target(body: TargetConfig):
        """Save a target config to config/targets/; return updated targets list."""
        path = save_target_config(body, config_dir=_targets_dir())
        return {"saved": path, "targets": _load_targets()}

    return app
