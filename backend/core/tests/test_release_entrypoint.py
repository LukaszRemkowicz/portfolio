from unittest.mock import Mock, call

import pytest

from scripts import release_entrypoint


@pytest.mark.parametrize("environment", ["prod", "production"])
def test_production_release_repairs_empty_travel_country_after_backfill(monkeypatch, environment):
    run = Mock()
    monkeypatch.setattr(release_entrypoint.subprocess, "run", run)
    monkeypatch.setenv("ENVIRONMENT", environment)

    assert release_entrypoint.main() == 0

    assert run.call_args_list == [
        call(
            (
                release_entrypoint.sys.executable,
                "manage.py",
                "backfill_image_variants",
                "--verbosity",
                "0",
                "--silent",
            ),
            check=True,
        ),
        call(
            (
                release_entrypoint.sys.executable,
                "manage.py",
                "repair_travel_place",
                "--place-id",
                "53",
                "--country",
                "PL",
                "--apply",
                "--if-country-empty",
            ),
            check=True,
        ),
    ]


@pytest.mark.parametrize("environment", ["stage", "dev"])
def test_nonproduction_release_only_runs_existing_backfill(monkeypatch, environment):
    run = Mock()
    monkeypatch.setattr(release_entrypoint.subprocess, "run", run)
    monkeypatch.setenv("ENVIRONMENT", environment)

    assert release_entrypoint.main() == 0

    assert run.call_args_list == [
        call(
            (
                release_entrypoint.sys.executable,
                "manage.py",
                "backfill_image_variants",
                "--verbosity",
                "0",
                "--silent",
            ),
            check=True,
        )
    ]


def test_release_stops_when_a_configuration_command_fails(monkeypatch):
    run = Mock(side_effect=release_entrypoint.subprocess.CalledProcessError(1, "manage.py"))
    monkeypatch.setattr(release_entrypoint.subprocess, "run", run)
    monkeypatch.setenv("ENVIRONMENT", "prod")

    with pytest.raises(release_entrypoint.subprocess.CalledProcessError):
        release_entrypoint.main()

    assert run.call_count == 1
