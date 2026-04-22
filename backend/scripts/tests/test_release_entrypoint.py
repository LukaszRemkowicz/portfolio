import sys

from pytest_mock import MockerFixture

from scripts.release_entrypoint import RELEASE_CONFIGURATION_COMMANDS, main


def test_release_entrypoint_commands_include_baseimage_backfill() -> None:
    assert RELEASE_CONFIGURATION_COMMANDS == (
        (sys.executable, "manage.py", "backfill_baseimage_fields", "--verbosity", "0"),
    )


def test_release_entrypoint_runs_commands_in_order(mocker: MockerFixture) -> None:
    run_mock = mocker.patch("scripts.release_entrypoint.subprocess.run")

    result = main()

    assert result == 0
    assert run_mock.call_args_list == [
        mocker.call(
            (sys.executable, "manage.py", "backfill_baseimage_fields", "--verbosity", "0"),
            check=True,
        ),
    ]
