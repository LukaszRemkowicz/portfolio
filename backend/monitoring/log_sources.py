import json
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class LogSource:
    key: str
    filename: str
    required: bool
    service_env: str
    service_default: str
    model_field: str
    prompt_section: str
    compose_project_env: str | None = None
    compose_project_default: str | None = None
    container_name_env: str | None = None
    container_name_default: str | None = None


def _load_log_sources() -> tuple[LogSource, ...]:
    manifest_path = Path(__file__).with_name("log_sources.json")
    with manifest_path.open(encoding="utf-8") as manifest_file:
        payload = json.load(manifest_file)
    return tuple(LogSource(**item) for item in payload)


LOG_SOURCES = _load_log_sources()
LOG_SOURCES_BY_KEY = {source.key: source for source in LOG_SOURCES}
REQUIRED_LOG_SOURCE = next(source for source in LOG_SOURCES if source.required)
