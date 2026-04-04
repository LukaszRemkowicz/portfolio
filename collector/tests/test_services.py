from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from log_collector.config import CollectorSettings
from log_collector.services import CollectorApplicationService
from log_collector.types import LogSourceDefinition, ResolvedContainer


@dataclass
class FakeDockerGateway:
    logs_by_container: dict[str, str]
    resolved_by_service: dict[tuple[str, str], ResolvedContainer]
    resolved_by_name: dict[str, ResolvedContainer]

    def resolve_container_by_project_service(
        self,
        *,
        project_name: str,
        service_name: str,
    ) -> ResolvedContainer | None:
        return self.resolved_by_service.get((project_name, service_name))

    def resolve_container_by_name(self, container_name: str) -> ResolvedContainer | None:
        return self.resolved_by_name.get(container_name)

    def fetch_logs(
        self,
        *,
        container_name: str,
        tail: int,
        since: datetime,
        timestamps: bool,
    ) -> str:
        return self.logs_by_container[container_name]


def test_run_writes_logs_and_metadata(tmp_path: Path) -> None:
    logs_dir = tmp_path / "logs"
    settings = CollectorSettings(
        logs_dir=logs_dir,
        compose_file=Path("/tmp/docker-compose.prod.yml"),
        environment="prod",
        project_name="portfolio-prod",
        log_tail=5000,
        log_since="24h",
        archive_retention_days=30,
        docker_tool_log=logs_dir / "docker-tool-errors.log",
        manifest_path=Path("/tmp/log_sources.json"),
    )
    source = LogSourceDefinition(
        key="backend",
        filename="backend.log",
        required=True,
        service_env="BACKEND_SERVICE",
        service_default="be",
    )
    gateway = FakeDockerGateway(
        logs_by_container={"portfolio-prod-be-1": "line-1\nline-2\n"},
        resolved_by_service={
            ("portfolio-prod", "be"): ResolvedContainer(
                name="portfolio-prod-be-1",
                created_at=datetime(2026, 4, 2, tzinfo=UTC),
            )
        },
        resolved_by_name={},
    )

    service = CollectorApplicationService(
        settings=settings,
        docker_gateway=gateway,
        log_sources=[source],
    )
    result = service.run()

    assert result.total_bytes == len("line-1\nline-2\n")
    assert (logs_dir / "backend.log").exists()
    assert (logs_dir / "collected_at.txt").exists()


def test_run_archives_previous_snapshot(tmp_path: Path) -> None:
    logs_dir = tmp_path / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)
    (logs_dir / "backend.log").write_text("old backend", encoding="utf-8")
    (logs_dir / "collected_at.txt").write_text("2026-04-01T00:00:00Z", encoding="utf-8")

    settings = CollectorSettings(
        logs_dir=logs_dir,
        compose_file=Path("/tmp/docker-compose.prod.yml"),
        environment="prod",
        project_name="portfolio-prod",
        log_tail=5000,
        log_since="24h",
        archive_retention_days=30,
        docker_tool_log=logs_dir / "docker-tool-errors.log",
        manifest_path=Path("/tmp/log_sources.json"),
    )
    gateway = FakeDockerGateway(
        logs_by_container={},
        resolved_by_service={},
        resolved_by_name={},
    )
    source = LogSourceDefinition(
        key="backend",
        filename="backend.log",
        required=True,
        service_env="BACKEND_SERVICE",
        service_default="be",
    )

    service = CollectorApplicationService(
        settings=settings,
        docker_gateway=gateway,
        log_sources=[source],
    )
    service.run()

    archive_root = logs_dir / "archive"
    assert archive_root.exists()
    assert any(path.is_dir() for path in archive_root.iterdir())


def test_run_reads_file_backed_sources(monkeypatch, tmp_path: Path) -> None:
    logs_dir = tmp_path / "logs"
    source_log = tmp_path / "traefik-access.log"
    source_log.write_text("line-1\nline-2\nline-3\n", encoding="utf-8")
    monkeypatch.delenv("TRAEFIK_ACCESS_LOG_PATH", raising=False)

    settings = CollectorSettings(
        logs_dir=logs_dir,
        compose_file=Path("/tmp/docker-compose.prod.yml"),
        environment="prod",
        project_name="portfolio-prod",
        log_tail=2,
        log_since="24h",
        archive_retention_days=30,
        docker_tool_log=logs_dir / "docker-tool-errors.log",
        manifest_path=Path("/tmp/log_sources.json"),
    )
    gateway = FakeDockerGateway(
        logs_by_container={},
        resolved_by_service={},
        resolved_by_name={},
    )
    source = LogSourceDefinition(
        key="traefik_access",
        filename="traefik_access.log",
        required=False,
        source_type="file",
        service_env="TRAEFIK_SERVICE",
        service_default="traefik",
        file_path_env="TRAEFIK_ACCESS_LOG_PATH",
        file_path_default=str(source_log),
    )

    service = CollectorApplicationService(
        settings=settings,
        docker_gateway=gateway,
        log_sources=[source],
    )
    service.run()

    assert (logs_dir / "traefik_access.log").read_text(encoding="utf-8") == "line-2\nline-3\n"
