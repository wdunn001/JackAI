"""Build TargetConfig from scan results; optionally save to config/targets/."""

import re
from pathlib import Path
from urllib.parse import urlparse

import yaml

from jackai.models.config import TargetConfig
from jackai.models.scanner import IdentifiedInteraction


def _safe_filename(url: str, widget_type: str, suffix: str = "") -> str:
    """Produce a safe filename from URL and widget type (e.g. discovered-example-com-1)."""
    parsed = urlparse(url)
    domain = (parsed.netloc or parsed.path or "unknown").replace(".", "-").lower()
    domain = re.sub(r"[^a-z0-9-]", "", domain)[:50]
    wt = re.sub(r"[^a-z0-9]", "", widget_type.lower())[:20]
    name = f"discovered-{domain}-{wt or 'generic'}{suffix}"
    return name


def build_target_config_from_result(
    identified: IdentifiedInteraction,
    success: bool,
    strategy_used: str,
    name: str | None = None,
) -> TargetConfig:
    """
    Build a TargetConfig from an IdentifiedInteraction and test result.
    Used by context-wipe test and by save-target.
    """
    rec_strategy = strategy_used if strategy_used else "new_session"
    if rec_strategy not in ("new_session", "inject", "api"):
        rec_strategy = "new_session"
    display_name = name or _safe_filename(identified.url, identified.widget_type)
    return TargetConfig(
        name=display_name,
        adapter_type="web_widget",
        url=identified.url,
        selectors=identified.selectors,
        recommended_context_strategy=rec_strategy,
        widget_type=identified.widget_type,
    )


def save_target_config(
    config: TargetConfig,
    config_dir: str | Path | None = None,
    filename: str | None = None,
) -> str:
    """
    Save TargetConfig to config/targets/ (or config_dir). Returns path written.
    """
    if config_dir is None:
        config_dir = Path("config") / "targets"
    else:
        config_dir = Path(config_dir)
    config_dir.mkdir(parents=True, exist_ok=True)
    if filename is None:
        filename = _safe_filename(config.url or "", config.widget_type or "generic", ".yaml")
    path = config_dir / filename
    data = config.model_dump(mode="json")
    with open(path, "w") as f:
        yaml.dump(data, f, default_flow_style=False, sort_keys=False)
    return str(path)
