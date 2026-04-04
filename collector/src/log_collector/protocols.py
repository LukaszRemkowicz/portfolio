"""Behavioral protocols for collector service boundaries.

Protocols keep the collector service decoupled from the concrete Docker SDK
adapter and make it easier to substitute fake implementations in tests.
"""

from __future__ import annotations

from datetime import datetime
from typing import Protocol, runtime_checkable

from .types import ResolvedContainer


@runtime_checkable
class DockerLogGateway(Protocol):
    """Container discovery and log retrieval contract for the collector."""

    def resolve_container_by_project_service(
        self,
        *,
        project_name: str,
        service_name: str,
    ) -> ResolvedContainer | None: ...

    def resolve_container_by_name(self, container_name: str) -> ResolvedContainer | None: ...

    def fetch_logs(
        self,
        *,
        container_name: str,
        tail: int,
        since: datetime,
        timestamps: bool,
    ) -> str: ...
