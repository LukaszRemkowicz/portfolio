import uuid

from translation.mixins import AutomatedTranslationModelMixin
from translation.models import TranslationTask
from translation.tasks import translate_instance_task


class TestTranslationDispatch:
    def test_trigger_translation_submits_background_task(self, mocker):
        """Translation dispatch goes through common.background.submit (commit-aware)."""
        mixin = AutomatedTranslationModelMixin()
        obj = mocker.Mock()
        obj.pk = "image-1"
        obj._meta.label = "astrophotography.AstroImage"
        content_type = mocker.Mock()

        task_manager = mocker.patch("translation.mixins.TranslationTask.objects")
        task_manager.filter.return_value.delete.return_value = (0, {})
        task_manager.update_or_create.return_value = (mocker.Mock(), True)
        mocker.patch("uuid.uuid4", return_value=uuid.UUID(int=7))
        submit = mocker.patch("translation.mixins.submit")

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
        submit.assert_called_once_with(
            translate_instance_task,
            retries=3,
            retry_delay=60,
            task_id=task_id,
            model_name=obj._meta.label,
            instance_pk=obj.pk,
            language_code="pl",
            method_name="translate_astro_image",
        )
