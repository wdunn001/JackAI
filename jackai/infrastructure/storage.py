"""Storage configuration: TinyDB path and init."""

import os
from pathlib import Path


def get_db_path() -> Path:
    """Return the TinyDB file path. Uses JACKAI_DB_PATH env or default data/jackai.json."""
    default = Path("data") / "jackai.json"
    path = os.environ.get("JACKAI_DB_PATH", str(default))
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    return p
