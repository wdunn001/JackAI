"""Load target configs from config/targets/ (shared by API and CLI)."""

from pathlib import Path

import yaml

from jackai.models.config import TargetConfig


def get_targets_dir() -> Path:
    return Path("config") / "targets"


def load_targets(config_dir: Path | None = None) -> list[TargetConfig]:
    """Load all target configs from config/targets/ (or config_dir)."""
    if config_dir is None:
        config_dir = get_targets_dir()
    targets: list[TargetConfig] = []
    if not config_dir.exists():
        return targets
    for path in config_dir.glob("*.yaml"):
        try:
            with open(path) as f:
                data = yaml.safe_load(f)
            if data:
                targets.append(TargetConfig.model_validate(data))
        except Exception:
            continue
    return targets
