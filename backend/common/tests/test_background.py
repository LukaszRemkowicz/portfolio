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


def test_async_mode_retries_via_timer_then_logs(settings, mocker):
    settings.BACKGROUND_TASKS_SYNC = False
    close = mocker.patch("common.background.connection.close")
    reopen = mocker.patch("common.background.close_old_connections")
    log = mocker.patch("common.background.logger.exception")
    timers: list[float] = []

    class ImmediateTimer:
        def __init__(self, delay, fn, args):
            timers.append(delay)
            self.fn, self.args, self.daemon = fn, args, False

        def start(self):
            self.fn(*self.args)

    mocker.patch("common.background.Timer", ImmediateTimer)
    mocker.patch(
        "common.background._get_executor",
        return_value=MagicMock(submit=lambda fn, *a: fn(*a)),
    )
    func = MagicMock(side_effect=ValueError("boom"))

    background.submit(func, retries=2, retry_delay=7)

    assert func.call_count == 3
    assert timers == [7, 7]
    log.assert_called_once()
    # Every attempt gets a fresh DB connection and closes it.
    assert reopen.call_count == close.call_count == 3


def test_submit_waits_for_commit(settings, mocker):
    settings.BACKGROUND_TASKS_SYNC = True
    callbacks: list = []
    mocker.patch("common.background.transaction.on_commit", side_effect=callbacks.append)
    func = MagicMock()

    background.submit(func, "x")

    func.assert_not_called()
    callbacks[0]()
    func.assert_called_once_with("x")


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
