"""In-process background task runner (replaces Celery).

Tasks are plain functions submitted to a small thread pool after the current
transaction commits. A failed task is retried after a fixed delay (the Celery
tasks used a fixed countdown too). Tasks are lost if the process dies before
they run.
"""

import logging
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from threading import Lock, Timer
from typing import Any

from django.conf import settings
from django.db import close_old_connections, connection, transaction

logger = logging.getLogger(__name__)

_executor: ThreadPoolExecutor | None = None
_executor_lock = Lock()


def _get_executor() -> ThreadPoolExecutor:
    global _executor
    with _executor_lock:
        if _executor is None:
            _executor = ThreadPoolExecutor(
                max_workers=settings.BACKGROUND_TASK_WORKERS, thread_name_prefix="background"
            )
        return _executor


def _run(
    func: Callable[..., Any],
    args: tuple[Any, ...],
    kwargs: dict[str, Any],
    retries: int,
    delay: float,
) -> None:
    close_old_connections()
    try:
        func(*args, **kwargs)
    except Exception:
        if retries > 0:
            # A timer waits for the retry, so the delay does not hold a pool thread.
            timer = Timer(delay, _schedule, (func, args, kwargs, retries - 1, delay))
            timer.daemon = True
            timer.start()
        else:
            logger.exception("Background task %s failed", getattr(func, "__name__", func))
    finally:
        connection.close()


def _schedule(
    func: Callable[..., Any],
    args: tuple[Any, ...],
    kwargs: dict[str, Any],
    retries: int,
    delay: float,
) -> None:
    _get_executor().submit(_run, func, args, kwargs, retries, delay)


def submit(
    func: Callable[..., Any],
    *args: Any,
    retries: int = 0,
    retry_delay: float = 60,
    **kwargs: Any,
) -> None:
    """Run func in a background thread once the current transaction commits."""

    def dispatch() -> None:
        if settings.BACKGROUND_TASKS_SYNC:
            func(*args, **kwargs)
        else:
            _schedule(func, args, kwargs, retries, retry_delay)

    transaction.on_commit(dispatch)
