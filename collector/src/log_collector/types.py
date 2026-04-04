"""Domain types for the standalone log collector.

These classes model the collector's internal value objects and typed results.
They are intentionally lightweight and independent from Docker SDK types.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path


@dataclass(frozen=True)
class LogSourceDefinition:
    """Configuration for one collected log source from the manifest."""

    key: str
    filename: str
    required: bool
    service_env: str
    service_default: str
    source_type: str = "docker"
    compose_project_env: str = ""
    compose_project_default: str = ""
    container_name_env: str = ""
    container_name_default: str = ""
    file_path_env: str = ""
    file_path_default: str = ""


@dataclass(frozen=True)
class ResolvedContainer:
    """Container selected for a given log source lookup."""

    name: str
    created_at: datetime


@dataclass(frozen=True)
class SourceCollectionResult:
    """Per-source collection result written during a snapshot run."""

    source_key: str
    output_file: Path
    bytes_written: int
    container_name: str | None = None
    warning: str = ""


@dataclass(frozen=True)
class SnapshotCollectionResult:
    """Aggregated result of one full snapshot run."""

    collected_at: datetime
    total_bytes: int
    source_results: tuple[SourceCollectionResult, ...] = field(default_factory=tuple)


class CollectorConfigurationError(ValueError):
    """Raised when collector configuration is invalid."""


class DockerCollectionError(RuntimeError):
    """Raised when Docker API access fails."""
