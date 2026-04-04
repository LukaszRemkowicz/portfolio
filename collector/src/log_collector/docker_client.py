"""Docker SDK adapter used by the standalone collector.

This module isolates direct Docker SDK usage from the rest of the application.
The collector service depends on the higher-level ``DockerLogGateway`` protocol,
while this module provides the default SDK-backed implementation and factory.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, cast

from .protocols import DockerLogGateway
from .types import DockerCollectionError, ResolvedContainer


class DockerSDKLogGateway:
    """SDK-backed implementation of the collector's Docker gateway.

    The class keeps Docker SDK calls in one place so the rest of the collector
    works with typed domain objects and protocol-based abstractions rather than
    raw SDK responses.
    """

    def __init__(self, client: Any) -> None:
        """Store the Docker SDK client used for container queries and logs."""
        self.client = client

    @classmethod
    def from_env(cls) -> "DockerSDKLogGateway":
        """Create the gateway from the current Docker environment settings.

        This mirrors Docker SDK's standard ``from_env`` flow so the collector
        can respect the mounted socket or configured daemon host at runtime.
        """
        try:
            from docker import from_env as docker_from_env
        except ImportError as exc:
            raise DockerCollectionError(
                "The docker package is required for the collector runtime"
            ) from exc

        try:
            client: Any = docker_from_env()
            return cls(client=client)
        except Exception as exc:  # pragma: no cover - depends on Docker runtime
            raise DockerCollectionError(f"Unable to connect to Docker daemon: {exc}") from exc

    def resolve_container_by_project_service(
        self,
        *,
        project_name: str,
        service_name: str,
    ) -> ResolvedContainer | None:
        """Return the newest running container for a compose project/service pair."""
        filters = {
            "label": [
                f"com.docker.compose.project={project_name}",
                f"com.docker.compose.service={service_name}",
            ]
        }
        containers = self._list_running_containers(filters=filters)
        return self._newest_container(containers)

    def resolve_container_by_name(self, container_name: str) -> ResolvedContainer | None:
        """Return the newest running container matching an exact container name."""
        containers = self._list_running_containers(filters={"name": container_name})
        exact_matches = [
            container for container in containers if self._container_name(container) == container_name
        ]
        return self._newest_container(exact_matches)

    def fetch_logs(
        self,
        *,
        container_name: str,
        tail: int,
        since: datetime,
        timestamps: bool,
    ) -> str:
        """Fetch logs for a single resolved container."""
        try:
            container = self.client.containers.get(container_name)
            raw_output = container.logs(
                stdout=True,
                stderr=True,
                timestamps=timestamps,
                tail=tail,
                since=since,
            )
        except Exception as exc:  # pragma: no cover - depends on Docker runtime
            raise DockerCollectionError(
                f"Unable to read logs for container {container_name}: {exc}"
            ) from exc

        if isinstance(raw_output, bytes):
            return raw_output.decode("utf-8", errors="replace")
        return str(raw_output)

    def _list_running_containers(self, *, filters: dict[str, Any]) -> list[Any]:
        try:
            return list(self.client.containers.list(all=False, filters=filters))
        except Exception as exc:  # pragma: no cover - depends on Docker runtime
            raise DockerCollectionError(f"Unable to query Docker containers: {exc}") from exc

    def _newest_container(self, containers: list[Any]) -> ResolvedContainer | None:
        if not containers:
            return None
        newest = max(containers, key=self._created_at)
        return ResolvedContainer(
            name=self._container_name(newest),
            created_at=self._created_at(newest),
        )

    @staticmethod
    def _container_name(container: Any) -> str:
        name = getattr(container, "name", "")
        if name:
            return str(name)
        attrs = getattr(container, "attrs", {})
        return str(attrs.get("Name", "")).removeprefix("/")

    @staticmethod
    def _created_at(container: Any) -> datetime:
        attrs = getattr(container, "attrs", {})
        raw_created = str(attrs.get("Created", "")).strip()
        if not raw_created:
            return datetime.min.replace(tzinfo=UTC)

        normalized = raw_created.replace("Z", "+00:00")
        try:
            created_at = datetime.fromisoformat(normalized)
        except ValueError:
            return datetime.min.replace(tzinfo=UTC)

        if created_at.tzinfo is None:
            return created_at.replace(tzinfo=UTC)
        return created_at.astimezone(UTC)


def build_docker_gateway() -> DockerLogGateway:
    """Create the default Docker log gateway for the collector runtime.

    The returned object satisfies the collector's protocol boundary while
    keeping the concrete SDK implementation local to this module.
    """
    gateway: DockerSDKLogGateway = DockerSDKLogGateway.from_env()
    return cast(DockerLogGateway, gateway)
