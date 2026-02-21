"""Domain layer: entities and repository interfaces."""

from jackai.domain.entities import ScanRun
from jackai.domain.repositories import ScanHistoryRepository, TargetRepository

__all__ = [
    "ScanRun",
    "TargetRepository",
    "ScanHistoryRepository",
]
