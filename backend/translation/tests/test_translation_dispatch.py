import uuid

from translation.mixins import AutomatedTranslationModelMixin
from translation.models import TranslationTask


class TestTranslationDispatch:
    def test_trigger_translation_defers_celery_dispatch_until_commit(self, mocker):
        """Translation dispatch should wait for the model transaction to commit."""
        mixin = AutomatedTranslationModelMixin()
        obj = mocker.Mock()
        obj.pk = "image-1"
        obj._meta.label = "astrophotography.AstroImage"
        content_type = mocker.Mock()

        task_manager = mocker.patch("translation.mixins.TranslationTask.objects")
        task_manager.filter.return_value.delete.return_value = (0, {})
        task_manager.update_or_create.return_value = (mocker.Mock(), True)
        mocker.patch("uuid.uuid4", return_value=uuid.UUID(int=7))
        on_commit = mocker.patch("django.db.transaction.on_commit")
        apply_async = mocker.patch("translation.mixins.translate_instance_task.apply_async")

        task_id = mixin._trigger_translation(
            obj,
            "pl",
            content_type,
            "translate_astro_image",
        )

        assert task_id == "00000000-0000-0000-0000-000000000007"
        task_manager.update_or_create.assert_called_once()
        assert task_manager.update_or_create.call_args.kwargs["defaults"] == {
            "method": "translate_astro_image",
            "task_id": task_id,
            "status": TranslationTask.Status.PENDING,
        }
        apply_async.assert_not_called()

        on_commit.assert_called_once()
        on_commit.call_args.args[0]()

        apply_async.assert_called_once_with(
            kwargs={
                "model_name": obj._meta.label,
                "instance_pk": obj.pk,
                "language_code": "pl",
                "method_name": "translate_astro_image",
            },
            task_id=task_id,
        )
