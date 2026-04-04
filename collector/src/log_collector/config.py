"""Configuration and manifest loading for the collector app.

This module owns the collector's runtime configuration boundary:

- environment-backed settings loaded through pydantic-settings
- validation and normalization of paths, durations, and timezone names
- loading the bundled or overridden log source manifest

The rest of the collector should depend on typed settings objects rather than
reading environment variables directly.
"""

from __future__ import annotations

import json
import re
from datetime import timedelta
from importlib.resources import files
from pathlib import Path
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from .types import CollectorConfigurationError, LogSourceDefinition

_DURATION_RE = re.compile(r"^(?P<amount>\d+)(?P<unit>[smhd])$")
_ENVIRONMENT_RE = re.compile(r"docker-compose\.(?P<environment>.+)\.yml$")


class CollectorSettings(BaseSettings):
    """Validated environment-backed settings for the collector.

    Fields are sourced from environment variables so the collector can run as a
    standalone container or host-side command. Derived values, such as the
    compose project name and manifest path, are filled in after validation.
    """

    model_config = SettingsConfigDict(
        env_file=None,
        extra="ignore",
        case_sensitive=True,
        populate_by_name=True,
    )

    logs_dir: Path = Field(alias="DOCKER_LOGS_DIR")
    compose_file: Path | None = Field(default=None, alias="COMPOSE_FILE")
    environment: str | None = Field(default=None, alias="ENVIRONMENT")
    project_name: str | None = None
    compose_project_name: str | None = Field(default=None, alias="COMPOSE_PROJECT_NAME")
    log_tail: int = Field(default=5000, alias="LOG_TAIL", gt=0)
    log_since: str = Field(default="24h", alias="LOG_SINCE")
    archive_retention_days: int = Field(default=30, alias="ARCHIVE_RETENTION_DAYS", gt=0)
    docker_tool_log: Path | None = Field(default=None, alias="DOCKER_TOOL_LOG")
    manifest_path: Path | None = Field(default=None, alias="LOG_SOURCES_MANIFEST")
    timezone_name: str = Field(default="Europe/Warsaw", alias="TZ")

    @field_validator("logs_dir", "compose_file", "docker_tool_log", "manifest_path", mode="before")
    @classmethod
    def _expand_path(cls, value: object) -> object:
        if value is None:
            return value
        if isinstance(value, Path):
            return value.expanduser()
        if isinstance(value, str):
            stripped_value = value.strip()
            if not stripped_value:
                return None
            return Path(stripped_value).expanduser()
        return value

    @field_validator("environment", "compose_project_name", mode="before")
    @classmethod
    def _strip_optional_text(cls, value: object) -> object:
        if value is None:
            return value
        if isinstance(value, str):
            stripped_value = value.strip()
            return stripped_value or None
        return value

    @field_validator("log_since")
    @classmethod
    def _validate_log_since(cls, value: str) -> str:
        if not _DURATION_RE.match(value.strip()):
            raise ValueError("must use a duration like 15m, 12h, or 7d")
        return value.strip()

    @field_validator("timezone_name")
    @classmethod
    def _validate_timezone_name(cls, value: str) -> str:
        normalized_value = value.strip()
        try:
            ZoneInfo(normalized_value)
        except ZoneInfoNotFoundError as exc:
            raise ValueError(f"unknown timezone: {normalized_value}") from exc
        return normalized_value

    @model_validator(mode="after")
    def _populate_derived_fields(self) -> "CollectorSettings":
        if self.environment is None:
            self.environment = _resolve_environment(self.compose_file)

        if self.project_name is None:
            self.project_name = _resolve_project_name(
                compose_file=self.compose_file,
                environment=self.environment,
                compose_project_name=self.compose_project_name,
            )

        if self.manifest_path is None:
            self.manifest_path = Path(_default_manifest_path()).expanduser()

        if self.docker_tool_log is None:
            self.docker_tool_log = self.logs_dir / "docker-tool-errors.log"

        return self

    @property
    def timezone(self) -> ZoneInfo:
        """Return the configured IANA timezone."""
        return ZoneInfo(self.timezone_name)


def load_settings() -> CollectorSettings:
    """Load and validate collector settings from the current environment.

    Returns:
        A validated ``CollectorSettings`` instance ready for runtime use.

    Raises:
        CollectorConfigurationError: If any required or derived setting is
            invalid.
    """
    try:
        return CollectorSettings()
    except Exception as exc:
        raise CollectorConfigurationError(str(exc)) from exc


def load_log_sources(manifest_path: Path) -> list[LogSourceDefinition]:
    """Load the JSON manifest describing which log sources to collect.

    Args:
        manifest_path: Path to the manifest JSON file.

    Returns:
        A list of typed ``LogSourceDefinition`` objects.

    Raises:
        CollectorConfigurationError: If the manifest is missing or malformed.
    """
    if not manifest_path.exists():
        raise CollectorConfigurationError(f"Log sources manifest not found: {manifest_path}")

    with manifest_path.open(encoding="utf-8") as manifest_file:
        raw_sources = json.load(manifest_file)

    if not isinstance(raw_sources, list):
        raise CollectorConfigurationError("Log sources manifest must contain a list of sources")

    return [
        LogSourceDefinition(
            key=str(item["key"]),
            filename=str(item["filename"]),
            required=bool(item.get("required", False)),
            source_type=str(item.get("source_type", "docker")),
            service_env=str(item["service_env"]),
            service_default=str(item["service_default"]),
            compose_project_env=str(item.get("compose_project_env", "")),
            compose_project_default=str(item.get("compose_project_default", "")),
            container_name_env=str(item.get("container_name_env", "")),
            container_name_default=str(item.get("container_name_default", "")),
            file_path_env=str(item.get("file_path_env", "")),
            file_path_default=str(item.get("file_path_default", "")),
        )
        for item in raw_sources
    ]


def parse_since_duration(raw_value: str) -> timedelta:
    """Convert a collector duration string like ``24h`` into a ``timedelta``.

    The accepted format mirrors the previous shell collector contract:
    ``<number><unit>`` where unit is one of ``s``, ``m``, ``h``, or ``d``.
    """
    match = _DURATION_RE.match(raw_value.strip())
    if not match:
        raise CollectorConfigurationError(f"Invalid LOG_SINCE duration: {raw_value}")

    amount = int(match.group("amount"))
    unit = match.group("unit")
    multipliers = {
        "s": timedelta(seconds=amount),
        "m": timedelta(minutes=amount),
        "h": timedelta(hours=amount),
        "d": timedelta(days=amount),
    }
    return multipliers[unit]


def _resolve_environment(compose_file: Path) -> str:
    if compose_file is None:
        return "prod"
    match = _ENVIRONMENT_RE.search(compose_file.name)
    if match:
        return match.group("environment")
    return "prod"


def _resolve_project_name(
    *,
    compose_file: Path | None,
    environment: str,
    compose_project_name: str | None,
) -> str:
    if compose_project_name:
        return _apply_environment_suffix(compose_project_name, environment)
    compose_name = _read_compose_name(compose_file)
    if compose_name:
        return _apply_environment_suffix(compose_name, environment)

    return _apply_environment_suffix(_repo_root().name, environment)


def _read_compose_name(compose_file: Path | None) -> str:
    if compose_file is None or not compose_file.exists():
        return ""

    for line in compose_file.read_text(encoding="utf-8").splitlines():
        stripped_line = line.strip()
        if stripped_line.startswith("name:"):
            _, raw_name = stripped_line.split(":", 1)
            return raw_name.strip().strip("'\"")
    return ""


def _apply_environment_suffix(base_name: str, environment: str) -> str:
    suffix = _environment_suffix(environment)
    if base_name.endswith(f"-{suffix}") or base_name == suffix:
        return base_name
    return f"{base_name}-{suffix}"


def _environment_suffix(environment: str) -> str:
    aliases = {
        "production": "prod",
        "prod": "prod",
        "staging": "stage",
        "stage": "stage",
        "stg": "stage",
    }
    return aliases.get(environment, environment)


def _default_manifest_path() -> str:
    return str(files("log_collector").joinpath("log_sources.json"))


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[3]
