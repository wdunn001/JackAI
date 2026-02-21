"""Load target configs from domain layer (TinyDB by default)."""

from pathlib import Path

from jackai.core.models.config import TargetConfig
from jackai.infrastructure.tinydb_repositories import get_target_repository


def get_targets_dir() -> Path:
    """Return the data directory (where TinyDB file lives)."""
    from jackai.infrastructure.storage import get_db_path
    return get_db_path().parent


def load_targets(config_dir: Path | None = None) -> list[TargetConfig]:
    """Load all target configs from the domain store (TinyDB). config_dir ignored when using TinyDB."""
    return get_target_repository().list_all()
