"""Domain entities (storage-agnostic)."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class ScanRun(BaseModel):
    """Record of a scan pipeline run (full or single identify/test-wipe)."""

    id: str | None = Field(None, description="Optional stable id")
    kind: str = Field(..., description="e.g. full, identify, test_wipe")
    seeds: list[str] = Field(default_factory=list)
    url: str | None = None
    results_count: int = 0
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")
    extra: dict[str, Any] = Field(default_factory=dict)
