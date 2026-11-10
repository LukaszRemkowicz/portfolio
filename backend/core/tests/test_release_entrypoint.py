from unittest.mock import Mock, call

import pytest

from scripts import release_entrypoint


def test_release_runs_no_commands_by_default(monkeypatch):
    run = Mock()
    monkeypatch.setattr(release_entrypoint.subprocess, "run", run)

    assert release_entrypoint.main() == 0

    run.assert_not_called()


def test_release_runs_configured_commands_in_order(monkeypatch):
    run = Mock()
    monkeypatch.setattr(release_entrypoint.subprocess, "run", run)
    monkeypatch.setattr(
        release_entrypoint,
        "RELEASE_CONFIGURATION_COMMANDS",
        (("first", "--flag"), ("second",)),
    )

    assert release_entrypoint.main() == 0

    assert run.call_args_list == [
        call((release_entrypoint.sys.executable, "manage.py", "first", "--flag"), check=True),
        call((release_entrypoint.sys.executable, "manage.py", "second"), check=True),
    ]


def test_release_stops_when_a_configuration_command_fails(monkeypatch):
    run = Mock(side_effect=release_entrypoint.subprocess.CalledProcessError(1, "manage.py"))
    monkeypatch.setattr(release_entrypoint.subprocess, "run", run)
    monkeypatch.setattr(
        release_entrypoint, "RELEASE_CONFIGURATION_COMMANDS", (("first",), ("second",))
    )

    with pytest.raises(release_entrypoint.subprocess.CalledProcessError):
        release_entrypoint.main()

    assert run.call_count == 1
