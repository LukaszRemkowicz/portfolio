"""CLI entrypoint for the standalone log collector.

This module wires together configuration loading, Docker gateway creation, and
the snapshot collection service, then emits structured runtime logs suitable
for Docker/container execution.
"""

import logging

from .config import CollectorSettings, load_log_sources, load_settings
from .docker_client import build_docker_gateway
from .protocols import DockerLogGateway
from .services import CollectorApplicationService
from .types import (
    CollectorConfigurationError,
    DockerCollectionError,
    LogSourceDefinition,
    SnapshotCollectionResult,
)

logger = logging.getLogger(__name__)


def main() -> int:
    """Run one full collector cycle from the current environment configuration.

    Returns:
        Process exit code compatible with container or CLI usage.
    """
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    try:
        settings: CollectorSettings = load_settings()
        log_sources: list[LogSourceDefinition] = load_log_sources(settings.manifest_path)
        docker_gateway: DockerLogGateway = build_docker_gateway()
        application: CollectorApplicationService = CollectorApplicationService(
            settings=settings,
            docker_gateway=docker_gateway,
            log_sources=log_sources,
        )
        result: SnapshotCollectionResult = application.run()
    except (CollectorConfigurationError, DockerCollectionError) as exc:
        logger.exception("Collector run failed: %s", exc)
        return 1

    logger.info(
        "Collected log snapshot at "
        f"{result.collected_at.isoformat().replace('+00:00', 'Z')} "
        f"({result.total_bytes} bytes)"
    )
    for source_result in result.source_results:
        container_display = source_result.container_name or "none"
        warning_suffix = f" warning={source_result.warning}" if source_result.warning else ""
        logger.info(
            f"- {source_result.source_key}: {source_result.bytes_written} bytes "
            f"container={container_display}{warning_suffix}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
