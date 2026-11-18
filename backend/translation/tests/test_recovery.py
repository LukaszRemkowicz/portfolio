from io import StringIO
from unittest.mock import MagicMock

import pytest

from django.contrib.contenttypes.models import ContentType
from django.core.management import call_command

from astrophotography.tests.factories import PlaceFactory
from translation.models import TranslationTask
from translation.services import TranslationService


@pytest.mark.django_db
def test_reset_stuck_tasks_only_updates_pending_and_running():
    place = PlaceFactory()
    content_type = ContentType.objects.get_for_model(place)
    tasks = [
        TranslationTask.objects.create(
            task_id=status,
            content_type=content_type,
            object_id=str(place.pk),
            language="pl",
            method="translate",
            status=status,
        )
        for status in TranslationTask.Status.values
    ]
    call_command("reset_stuck_translation_tasks", stdout=StringIO())
    for task in tasks:
        task.refresh_from_db()
        if task.task_id in ("PENDING", "RUNNING"):
            assert task.status == "FAILED"
            assert "interrupted" in task.error_message.lower()
        else:
            assert task.status == task.task_id


@pytest.mark.django_db
def test_translation_save_failure_propagates():
    instance = MagicMock()
    instance.save_translations.side_effect = ValueError("save failed")
    with pytest.raises(ValueError, match="save failed"):
        TranslationService._save_translations(MagicMock(), instance, "Example")


@pytest.mark.django_db
@pytest.mark.parametrize("succeed_on_retry", [False, True])
def test_translation_retry_tracks_terminal_failure_or_success(mocker, settings, succeed_on_retry):
    from requests.exceptions import RequestException

    from common import background

    place = PlaceFactory()
    content_type = ContentType.objects.get_for_model(place)
    settings.BACKGROUND_TASKS_SYNC = False
    mocker.patch("translation.mixins.submit", background.submit)
    mocker.patch("common.background.close_old_connections")
    mocker.patch("common.background.connection.close")
    mocker.patch(
        "common.background._get_executor", return_value=MagicMock(submit=lambda fn, *a: fn(*a))
    )
    timers = []

    class DeferredTimer:
        def __init__(self, delay, fn, args):
            self.fn, self.args, self.daemon = fn, args, False

        def start(self):
            timers.append(self)

    mocker.patch("common.background.Timer", DeferredTimer)
    service = MagicMock()
    service.translate_place.side_effect = (
        [RequestException("offline"), ({}, {})] if succeed_on_retry else RequestException("offline")
    )
    mocker.patch("translation.tasks.TranslationService.create_default", return_value=service)
    task_id = place._trigger_translation(place, "pl", content_type, "translate_place")
    task = TranslationTask.objects.get(task_id=task_id)
    assert task.status == TranslationTask.Status.RUNNING
    while timers:
        timer = timers.pop(0)
        timer.fn(*timer.args)
    task.refresh_from_db()
    if succeed_on_retry:
        assert task.status == TranslationTask.Status.COMPLETED
        assert not task.error_message
    else:
        assert task.status == TranslationTask.Status.FAILED
        assert task.error_message == "offline"


@pytest.mark.django_db
def test_persistence_failure_marks_exact_translation_task_failed(mocker):
    from translation.tasks import translate_instance_task

    place = PlaceFactory()
    content_type = ContentType.objects.get_for_model(place)
    tasks = [
        TranslationTask.objects.create(
            task_id=task_id,
            content_type=content_type,
            object_id=str(place.pk),
            language="pl",
            method="translate_place",
        )
        for task_id in ("target", "other")
    ]
    failing_instance = MagicMock()
    failing_instance.save_translations.side_effect = ValueError("save failed")
    service = MagicMock()
    service.translate_place.side_effect = lambda *_args: TranslationService._save_translations(
        service, failing_instance, "Place"
    )
    mocker.patch("translation.tasks.TranslationService.create_default", return_value=service)
    translate_instance_task(
        "astrophotography.Place", place.pk, "pl", "translate_place", task_id="target"
    )
    for task in tasks:
        task.refresh_from_db()
    assert tasks[0].status == TranslationTask.Status.FAILED
    assert tasks[0].error_message == "save failed"
    assert tasks[1].status == TranslationTask.Status.PENDING
