"""CLI: scan + channel commands (connect, send, clear-context, set-context, disconnect)."""

from pathlib import Path

import typer
import yaml

from jackai.api.channels import get_registry
from jackai.core.config_loader import load_targets
from jackai.core.models.config import TargetConfig
from jackai.core.models.interface import ContextStrategy, SendRequest
from jackai.core.models.scanner import (
    ContextWipeTestResult,
    IdentifiedInteraction,
    ScrapeInput,
    ScrapeResult,
)
from jackai.scanner.adapter_factory import build_target_config_from_result, save_target_config
from jackai.scanner.identify import run_identify
from jackai.scanner.scrape import run_scrape
from jackai.scanner.test_context_wipe import run_context_wipe_test

app = typer.Typer(help="JackAI: PoC for context-hijacking of publicly exposed AIs")

scan_app = typer.Typer(help="Scrape sites, identify widgets, test context wipe, save targets")
app.add_typer(scan_app, name="scan")


@app.command("serve")
def serve_cmd(
    host: str = typer.Option("127.0.0.1", "--host", "-h"),
    port: int = typer.Option(8000, "--port", "-p"),
) -> None:
    """Run the FastAPI backend (uvicorn)."""
    import logging
    import uvicorn
    from jackai.api.app import create_app

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    uvicorn.run(
        create_app(),
        host=host,
        port=port,
        log_level="info",
    )


@app.command("connect")
def connect_cmd(
    target_name: str = typer.Argument(..., help="Target name (from config/targets/)"),
) -> None:
    """Connect to a channel by target name."""
    targets = load_targets()
    config = next((t for t in targets if t.name == target_name), None)
    if not config:
        typer.echo(f"Target {target_name!r} not found. List targets from config/targets/.", err=True)
        raise typer.Exit(1)
    try:
        get_registry().connect(target_name, config)
        typer.echo(f"Connected to {target_name}.")
    except Exception as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1)


@app.command("disconnect")
def disconnect_cmd(
    target_name: str | None = typer.Argument(None, help="Target name (omit to disconnect all)"),
) -> None:
    """Disconnect a channel (or all if no name given)."""
    registry = get_registry()
    if target_name:
        registry.disconnect(target_name)
        typer.echo(f"Disconnected {target_name}.")
    else:
        for cid in list(registry.connected_ids()):
            registry.disconnect(cid)
        typer.echo("Disconnected all.")


@app.command("send")
def send_cmd(
    message: str = typer.Argument(..., help="Message to send"),
    target: str | None = typer.Option(None, "--target", "-t", help="Target name (default: first connected)"),
) -> None:
    """Send a message to connected channel(s)."""
    registry = get_registry()
    if target:
        if not registry.is_connected(target):
            typer.echo(f"Target {target!r} not connected.", err=True)
            raise typer.Exit(1)
        ids = [target]
    else:
        ids = list(registry.connected_ids())
        if not ids:
            typer.echo("No channel connected. Use 'jackai connect <target>' first.", err=True)
            raise typer.Exit(1)
    for cid in ids:
        try:
            reply = registry.send(cid, SendRequest(content=message))
            typer.echo(f"[{cid}] {reply.content}")
        except Exception as e:
            typer.echo(f"[{cid}] Error: {e}", err=True)


@app.command("clear-context")
def clear_context_cmd(
    target: str = typer.Argument(..., help="Target name"),
    strategy: str = typer.Option("new_session", "--strategy", "-s", help="new_session | inject | api"),
    payload: str | None = typer.Option(None, "--payload", "-p", help="Injection payload when strategy=inject"),
) -> None:
    """Clear context on a channel."""
    registry = get_registry()
    if not registry.is_connected(target):
        typer.echo(f"Target {target!r} not connected.", err=True)
        raise typer.Exit(1)
    try:
        registry.clear_context(target, ContextStrategy(strategy=strategy, payload=payload))
        typer.echo(f"Context cleared on {target} (strategy={strategy}).")
    except Exception as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1)


@app.command("set-context")
def set_context_cmd(
    target: str = typer.Argument(..., help="Target name"),
    payload: str = typer.Argument(..., help="Injection payload to set context"),
) -> None:
    """Set context via injection payload on a channel."""
    registry = get_registry()
    if not registry.is_connected(target):
        typer.echo(f"Target {target!r} not connected.", err=True)
        raise typer.Exit(1)
    try:
        registry.set_context(target, payload)
        typer.echo(f"Context set on {target}.")
    except Exception as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1)


@scan_app.command("scrape")
def scan_scrape_cmd(
    urls: list[str] = typer.Argument(..., help="Seed URLs"),
    file: Path | None = typer.Option(None, "--file", "-f", help="File with one URL per line"),
    crawl_depth: int = typer.Option(0, "--crawl-depth", "-d", help="Same-origin crawl depth (0 = no crawl)"),
    sitemap: bool = typer.Option(False, "--sitemap", "-s", help="Try sitemap.xml for URLs"),
) -> None:
    """Collect URLs from seeds (optional crawl/sitemap). Output: one URL per line."""
    seeds = list(urls)
    if file and file.exists():
        seeds.extend([line.strip() for line in file.read_text().splitlines() if line.strip()])
    if not seeds:
        typer.echo("Provide URLs or --file", err=True)
        raise typer.Exit(1)
    input_data = ScrapeInput(seeds=seeds, crawl_depth=crawl_depth, use_sitemap=sitemap)
    result = run_scrape(input_data)
    for u in result.urls:
        typer.echo(u)


@scan_app.command("identify")
def scan_identify_cmd(
    url: str = typer.Argument(..., help="Page URL to analyze"),
    json_out: bool = typer.Option(False, "--json", "-j", help="Output as JSON"),
) -> None:
    """Detect chat widgets on a page. Output: identified interactions (table or JSON)."""
    identified = run_identify(url=url)
    if json_out:
        typer.echo([m.model_dump(mode="json") for m in identified])
        return
    if not identified:
        typer.echo("No widgets identified.")
        return
    for m in identified:
        typer.echo(f"  {m.widget_type} @ {m.url} (confidence={m.confidence})")


@scan_app.command("test-wipe")
def scan_test_wipe_cmd(
    url: str = typer.Argument(..., help="Page URL (must have been identified)"),
    json_out: bool = typer.Option(False, "--json", "-j", help="Output as JSON"),
) -> None:
    """Run context-wipe test on a URL (identifies first, then tests). Output: success + target config."""
    identified_list = run_identify(url=url)
    if not identified_list:
        typer.echo("No widgets identified on this URL.", err=True)
        raise typer.Exit(1)
    ident = identified_list[0]
    result = run_context_wipe_test(ident)
    if json_out:
        typer.echo(result.model_dump(mode="json"))
        return
    typer.echo(f"Success: {result.success}  Strategy: {result.strategy_used}")
    typer.echo(f"Target config: {result.target_config.model_dump(mode='json')}")


@scan_app.command("full")
def scan_full_cmd(
    urls: list[str] = typer.Argument(..., help="Seed URLs"),
    file: Path | None = typer.Option(None, "--file", "-f", help="File with one URL per line"),
    save: bool = typer.Option(False, "--save", "-s", help="Save discovered target configs to config/targets/"),
    json_out: bool = typer.Option(False, "--json", "-j", help="Output as JSON"),
) -> None:
    """Full pipeline: scrape -> identify -> test-wipe for each candidate. Optionally save target configs."""
    seeds = list(urls)
    if file and file.exists():
        seeds.extend([line.strip() for line in file.read_text().splitlines() if line.strip()])
    if not seeds:
        typer.echo("Provide URLs or --file", err=True)
        raise typer.Exit(1)
    input_data = ScrapeInput(seeds=seeds)
    scrape_result = run_scrape(input_data)
    all_identified: list[IdentifiedInteraction] = []
    for u in scrape_result.urls:
        all_identified.extend(run_identify(url=u))
    results: list[ContextWipeTestResult] = []
    for ident in all_identified:
        res = run_context_wipe_test(ident)
        results.append(res)
        if save and res.success:
            save_target_config(res.target_config, config_dir=Path("config") / "targets")
    if json_out:
        typer.echo({
            "results": [r.model_dump(mode="json") for r in results],
            "target_configs": [r.target_config.model_dump(mode="json") for r in results],
        })
        return
    for r in results:
        typer.echo(f"  {r.identified.url} -> success={r.success} strategy={r.strategy_used}")


@scan_app.command("save-target")
def scan_save_target_cmd(
    config_path: Path = typer.Argument(..., help="Path to target config YAML (or use stdin)"),
    stdin: bool = typer.Option(False, "--stdin", help="Read TargetConfig JSON from stdin"),
) -> None:
    """Save a target config to config/targets/. Input: path to YAML or --stdin JSON."""
    if stdin:
        import sys
        import json
        data = json.load(sys.stdin)
        config = TargetConfig.model_validate(data)
    else:
        if not config_path.exists():
            typer.echo(f"File not found: {config_path}", err=True)
            raise typer.Exit(1)
        with open(config_path) as f:
            data = yaml.safe_load(f)
        config = TargetConfig.model_validate(data)
    path = save_target_config(config, config_dir=Path("config") / "targets")
    typer.echo(f"Saved: {path}")


if __name__ == "__main__":
    app()
