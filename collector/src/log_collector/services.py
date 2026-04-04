"""Application services for the standalone log collector.

This module contains the orchestration layer that coordinates a single snapshot
run: archive rotation, container resolution, log retrieval, file writing, and
collection metadata output.
"""

from __future__ import annotations

import os
import shutil
from collections import deque
from datetime import datetime
from pathlib import Path

from .config import CollectorSettings, parse_since_duration
from .protocols import DockerLogGateway
from .types import (
    DockerCollectionError,
    LogSourceDefinition,
    ResolvedContainer,
    SnapshotCollectionResult,
    SourceCollectionResult,
)


class CollectorApplicationService:
    """Orchestrate one full snapshot collection run.

    The service keeps runtime workflow decisions in one place while delegating
    Docker-specific operations to the injected gateway implementation.
    """

    def __init__(
        self,
        settings: CollectorSettings,
        docker_gateway: DockerLogGateway,
        log_sources: list[LogSourceDefinition],
    ) -> None:
        self.settings: CollectorSettings = settings
        self.docker_gateway: DockerLogGateway = docker_gateway
        self.log_sources: list[LogSourceDefinition] = log_sources

    def run(self) -> SnapshotCollectionResult:
        """Collect one complete log snapshot and persist it to disk.

        Returns:
            A typed summary of the completed snapshot run.
        """
        self.settings.logs_dir.mkdir(parents=True, exist_ok=True)
        self.settings.docker_tool_log.parent.mkdir(parents=True, exist_ok=True)

        collected_at: datetime = datetime.now(self.settings.timezone).replace(microsecond=0)
        self._archive_existing_snapshots(timestamp=collected_at)
        self._prune_old_archives(reference_time=collected_at)

        source_results: list[SourceCollectionResult] = [
            self._collect_source(source, collected_at=collected_at) for source in self.log_sources
        ]
        self._write_collected_at(collected_at)

        total_bytes: int = sum(result.bytes_written for result in source_results)
        return SnapshotCollectionResult(
            collected_at=collected_at,
            total_bytes=total_bytes,
            source_results=tuple(source_results),
        )

    def _collect_source(
        self,
        source: LogSourceDefinition,
        collected_at: datetime,
    ) -> SourceCollectionResult:
        """Collect logs for a single configured source and write its output file."""
        if source.source_type == "file":
            return self._collect_file_source(source)

        service_name: str = os.environ.get(source.service_env, source.service_default)
        compose_project: str = self.settings.project_name
        if source.compose_project_env:
            compose_project = os.environ.get(
                source.compose_project_env,
                source.compose_project_default or compose_project,
            )
        explicit_container_name: str = ""
        if source.container_name_env:
            explicit_container_name = os.environ.get(
                source.container_name_env,
                source.container_name_default,
            )

        output_path: Path = self.settings.logs_dir / source.filename
        resolved_container: ResolvedContainer | None = self._resolve_container(
            compose_project=compose_project,
            explicit_container_name=explicit_container_name,
            service_name=service_name,
        )

        if resolved_container is None:
            output_path.write_text("", encoding="utf-8")
            return SourceCollectionResult(
                source_key=source.key,
                output_file=output_path,
                bytes_written=0,
                warning=(
                    "No running container found for "
                    f"project={compose_project} service={service_name}"
                ),
            )

        try:
            logs: str = self.docker_gateway.fetch_logs(
                container_name=resolved_container.name,
                tail=self.settings.log_tail,
                since=collected_at - parse_since_duration(self.settings.log_since),
                timestamps=True,
            )
        except DockerCollectionError as exc:
            self._append_tool_error(str(exc))
            output_path.write_text("", encoding="utf-8")
            return SourceCollectionResult(
                source_key=source.key,
                output_file=output_path,
                bytes_written=0,
                container_name=resolved_container.name,
                warning=str(exc),
            )

        output_path.write_text(logs, encoding="utf-8")
        return SourceCollectionResult(
            source_key=source.key,
            output_file=output_path,
            bytes_written=output_path.stat().st_size,
            container_name=resolved_container.name,
        )

    def _collect_file_source(self, source: LogSourceDefinition) -> SourceCollectionResult:
        """Collect logs for a file-backed source and write its snapshot output."""
        output_path: Path = self.settings.logs_dir / source.filename
        raw_file_path: str = os.environ.get(source.file_path_env, source.file_path_default)
        if not raw_file_path:
            output_path.write_text("", encoding="utf-8")
            return SourceCollectionResult(
                source_key=source.key,
                output_file=output_path,
                bytes_written=0,
                warning=f"No file path configured for file-backed source {source.key}",
            )

        source_path = Path(raw_file_path).expanduser()
        if not source_path.exists():
            output_path.write_text("", encoding="utf-8")
            return SourceCollectionResult(
                source_key=source.key,
                output_file=output_path,
                bytes_written=0,
                warning=f"Log file not found for {source.key}: {source_path}",
            )

        logs = self._read_last_lines(source_path, self.settings.log_tail)
        output_path.write_text(logs, encoding="utf-8")
        return SourceCollectionResult(
            source_key=source.key,
            output_file=output_path,
            bytes_written=output_path.stat().st_size,
        )

    def _read_last_lines(self, source_path: Path, limit: int) -> str:
        """Read the last ``limit`` lines from a text log file."""
        if limit <= 0:
            return ""

        lines: deque[str] = deque(maxlen=limit)
        with source_path.open(encoding="utf-8", errors="replace") as source_file:
            for line in source_file:
                lines.append(line)
        return "".join(lines)

    def _resolve_container(
        self,
        compose_project: str,
        explicit_container_name: str,
        service_name: str,
    ) -> ResolvedContainer | None:
        """Resolve the container to inspect for a configured log source."""
        if explicit_container_name:
            resolved = self.docker_gateway.resolve_container_by_name(explicit_container_name)
            if resolved is not None:
                return resolved

        return self.docker_gateway.resolve_container_by_project_service(
            project_name=compose_project,
            service_name=service_name,
        )

    def _archive_existing_snapshots(self, timestamp: datetime) -> None:
        """Move the current snapshot set into a timestamped archive directory."""
        existing_snapshot_paths = [
            self.settings.logs_dir / filename
            for filename in self._snapshot_filenames()
            if (self.settings.logs_dir / filename).exists()
        ]
        if not existing_snapshot_paths:
            return

        archive_dir = self.settings.logs_dir / "archive" / timestamp.strftime("%Y-%m-%d_%H%M%S")
        archive_dir.mkdir(parents=True, exist_ok=True)
        for snapshot_path in existing_snapshot_paths:
            shutil.move(str(snapshot_path), archive_dir / snapshot_path.name)

    def _snapshot_filenames(self) -> tuple[str, ...]:
        """Return the current snapshot filenames derived from configured sources."""
        source_filenames = [source.filename for source in self.log_sources]
        return tuple([*source_filenames, "collected_at.txt"])

    def _prune_old_archives(self, reference_time: datetime) -> None:
        """Delete archived snapshot directories older than the retention window."""
        archive_root = self.settings.logs_dir / "archive"
        archive_root.mkdir(parents=True, exist_ok=True)

        retention_seconds = self.settings.archive_retention_days * 24 * 60 * 60
        for archive_dir in archive_root.iterdir():
            if not archive_dir.is_dir():
                continue
            age_seconds = reference_time.timestamp() - archive_dir.stat().st_mtime
            if age_seconds > retention_seconds:
                shutil.rmtree(archive_dir)

    def _write_collected_at(self, collected_at: datetime) -> None:
        """Persist the snapshot timestamp used by downstream monitoring code."""
        collected_at_path = self.settings.logs_dir / "collected_at.txt"
        collected_at_path.write_text(
            collected_at.isoformat().replace("+00:00", "Z"),
            encoding="utf-8",
        )

    def _append_tool_error(self, message: str) -> None:
        """Append a Docker/tooling error line to the collector error log."""
        with self.settings.docker_tool_log.open("a", encoding="utf-8") as tool_log_file:
            timestamp = datetime.now(self.settings.timezone).replace(microsecond=0).isoformat()
            tool_log_file.write(f"[{timestamp}] {message}\n")
