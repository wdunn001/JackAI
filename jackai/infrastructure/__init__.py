"""Infrastructure: TinyDB-backed repository implementations and storage config."""

from jackai.infrastructure.storage import get_db_path
from jackai.infrastructure.tinydb_repositories import (
    TinyDBScanHistoryRepository,
    TinyDBTargetRepository,
    get_scan_history_repository,
    get_target_repository,
)

__all__ = [
    "get_db_path",
    "TinyDBTargetRepository",
    "TinyDBScanHistoryRepository",
    "get_target_repository",
    "get_scan_history_repository",
]
