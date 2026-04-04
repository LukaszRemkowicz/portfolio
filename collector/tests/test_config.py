from __future__ import annotations

from pathlib import Path

from log_collector.config import load_log_sources, load_settings, parse_since_duration


def test_parse_since_duration_supports_hours() -> None:
    assert parse_since_duration("24h").total_seconds() == 24 * 3600


def test_load_settings_infers_environment_and_project_name(
    monkeypatch,
    tmp_path: Path,
) -> None:
    compose_file = tmp_path / "docker-compose.stage.yml"
    compose_file.write_text("name: portfolio\n", encoding="utf-8")
    manifest_path = tmp_path / "log_sources.json"
    manifest_path.write_text("[]", encoding="utf-8")

    monkeypatch.setenv("DOCKER_LOGS_DIR", str(tmp_path / "logs"))
    monkeypatch.setenv("COMPOSE_FILE", str(compose_file))
    monkeypatch.setenv("LOG_SOURCES_MANIFEST", str(manifest_path))
    monkeypatch.delenv("ENVIRONMENT", raising=False)
    monkeypatch.delenv("COMPOSE_PROJECT_NAME", raising=False)

    settings = load_settings()

    assert settings.environment == "stage"
    assert settings.project_name == "portfolio-stage"


def test_load_settings_uses_explicit_compose_project_name_without_compose_file(
    monkeypatch,
    tmp_path: Path,
) -> None:
    manifest_path = tmp_path / "log_sources.json"
    manifest_path.write_text("[]", encoding="utf-8")

    monkeypatch.setenv("DOCKER_LOGS_DIR", str(tmp_path / "logs"))
    monkeypatch.setenv("COMPOSE_PROJECT_NAME", "portfolio-prod")
    monkeypatch.setenv("LOG_SOURCES_MANIFEST", str(manifest_path))
    monkeypatch.delenv("COMPOSE_FILE", raising=False)
    monkeypatch.delenv("ENVIRONMENT", raising=False)

    settings = load_settings()

    assert settings.environment == "prod"
    assert settings.project_name == "portfolio-prod"


def test_load_log_sources_reads_shared_manifest_shape(tmp_path: Path) -> None:
    manifest_path = tmp_path / "log_sources.json"
    manifest_path.write_text(
        '[{"key":"backend","filename":"backend.log","required":true,'
        '"source_type":"docker","service_env":"BACKEND_SERVICE","service_default":"be"},'
        '{"key":"traefik_access","filename":"traefik_access.log","required":false,'
        '"source_type":"file","service_env":"TRAEFIK_SERVICE","service_default":"traefik",'
        '"file_path_env":"TRAEFIK_ACCESS_LOG_PATH",'
        '"file_path_default":"/var/log/traefik/access.log"}]',
        encoding="utf-8",
    )

    sources = load_log_sources(manifest_path)

    assert len(sources) == 2
    assert sources[0].key == "backend"
    assert sources[0].source_type == "docker"
    assert sources[1].key == "traefik_access"
    assert sources[1].source_type == "file"
    assert sources[1].file_path_env == "TRAEFIK_ACCESS_LOG_PATH"
