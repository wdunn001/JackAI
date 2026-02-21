"""Repository interfaces for the domain layer (storage-agnostic)."""

from abc import ABC, abstractmethod
from typing import Protocol

from jackai.domain.entities import ScanRun


class TargetRepository(Protocol):
    """Abstract interface for storing and retrieving target configs."""

    def list_all(self) -> list:
        """Return all target configs (model type from core.models.config.TargetConfig)."""
        ...

    def get_by_name(self, name: str):
        """Return one target by name, or None."""
        ...

    def save(self, target: object) -> str:
        """Persist a target config. Return identifier/path."""
        ...

    def delete(self, name: str) -> bool:
        """Remove target by name. Return True if removed."""
        ...


class ScanHistoryRepository(ABC):
    """Abstract interface for storing scan run history."""

    @abstractmethod
    def add(self, run: ScanRun) -> str:
        """Store a scan run. Return id."""
        ...

    @abstractmethod
    def list_recent(self, limit: int = 50) -> list[ScanRun]:
        """Return most recent scan runs."""
        ...
