from unittest.mock import MagicMock

import pytest

from common import background


def test_sync_mode_runs_inline_and_propagates(settings):
    settings.BACKGROUND_TASKS_SYNC = True
    func = MagicMock()
    background.submit(func, 1, a=2)
    func.assert_called_once_with(1, a=2)

    with pytest.raises(ValueError, match="boom"):
        background.submit(MagicMock(side_effect=ValueError("boom")))


def test_async_mode_retries_then_logs_and_closes_connection(settings, mocker):
    settings.BACKGROUND_TASKS_SYNC = False
    mocker.patch("common.background.time.sleep")
    close = mocker.patch("common.background.connection.close")
    mocker.patch("common.background.close_old_connections")
    log = mocker.patch("common.background.logger.exception")
    func = MagicMock(side_effect=ValueError("boom"))
    mocker.patch(
        "common.background._get_executor",
        return_value=MagicMock(submit=lambda fn, *a: fn(*a)),
    )

    background.submit(func, retries=2, retry_delay=1)

    assert func.call_count == 3
    log.assert_called_once()
    close.assert_called_once()


def test_async_mode_runs_in_thread(settings):
    settings.BACKGROUND_TASKS_SYNC = False
    import threading

    done = threading.Event()
    names: list[str] = []

    def func() -> None:
        names.append(threading.current_thread().name)
        done.set()

    background.submit(func)
    assert done.wait(5)
    assert names[0].startswith("background")
