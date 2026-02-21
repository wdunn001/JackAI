"""TinyDB-backed implementations of domain repositories."""

from jackai.core.models.config import TargetConfig
from jackai.domain.entities import ScanRun
from jackai.domain.repositories import ScanHistoryRepository
from jackai.infrastructure.storage import get_db_path

_TARGETS_TABLE = "targets"
_SCAN_HISTORY_TABLE = "scan_history"

_target_repo: "TinyDBTargetRepository | None" = None
_scan_history_repo: "TinyDBScanHistoryRepository | None" = None


def get_target_repository() -> "TinyDBTargetRepository":
    """Return the default TinyDB-backed target repository (singleton)."""
    global _target_repo
    if _target_repo is None:
        _target_repo = TinyDBTargetRepository(get_db_path())
    return _target_repo


def get_scan_history_repository() -> "TinyDBScanHistoryRepository":
    """Return the default TinyDB-backed scan history repository (singleton)."""
    global _scan_history_repo
    if _scan_history_repo is None:
        _scan_history_repo = TinyDBScanHistoryRepository(get_db_path())
    return _scan_history_repo


class TinyDBTargetRepository:
    """Store target configs in TinyDB (table: targets)."""

    def __init__(self, db_path: "Path | str"):
        from pathlib import Path
        from tinydb import TinyDB
        self._path = Path(db_path)
        self._db = TinyDB(self._path)
        self._table = self._db.table(_TARGETS_TABLE)

    def list_all(self) -> list[TargetConfig]:
        docs = self._table.all()
        out: list[TargetConfig] = []
        for d in docs:
            try:
                out.append(TargetConfig.model_validate(d))
            except Exception:
                continue
        return out

    def get_by_name(self, name: str) -> TargetConfig | None:
        from tinydb import Query
        q = Query()
        found = self._table.get(q.name == name)
        if found is None:
            return None
        return TargetConfig.model_validate(found)

    def save(self, target: TargetConfig) -> str:
        from tinydb import Query
        data = target.model_dump(mode="json")
        q = Query()
        self._table.upsert(data, q.name == target.name)
        return target.name

    def delete(self, name: str) -> bool:
        from tinydb import Query
        q = Query()
        removed = self._table.remove(q.name == name)
        return len(removed) > 0


class TinyDBScanHistoryRepository(ScanHistoryRepository):
    """Store scan run history in TinyDB (table: scan_history)."""

    def __init__(self, db_path: "Path | str"):
        from pathlib import Path
        from tinydb import TinyDB
        self._path = Path(db_path)
        self._db = TinyDB(self._path)
        self._table = self._db.table(_SCAN_HISTORY_TABLE)

    def add(self, run: ScanRun) -> str:
        data = run.model_dump(mode="json")
        if not data.get("id"):
            data["id"] = f"scan_{len(self._table) + 1}_{id(run) % 100000}"
        doc_id = self._table.insert(data)
        return data.get("id", str(doc_id))

    def list_recent(self, limit: int = 50) -> list[ScanRun]:
        docs = self._table.all()
        docs = sorted(docs, key=lambda d: d.get("created_at", ""), reverse=True)[:limit]
        out: list[ScanRun] = []
        for d in docs:
            try:
                out.append(ScanRun.model_validate(d))
            except Exception:
                continue
        return out
