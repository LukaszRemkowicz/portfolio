from __future__ import annotations

from typing import Any

from celery import Task

from django.db import transaction


class CommitAwareTask(Task):
    """Celery task base with explicit transaction-aware dispatch helpers."""

    abstract = True

    def delay_on_commit(self, *args: Any, **kwargs: Any) -> None:
        transaction.on_commit(lambda: self.delay(*args, **kwargs))
