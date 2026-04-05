from io import StringIO

import pytest

from django.core.management import call_command
from django.test import override_settings

from astrophotography.tasks import (
    calculate_astroimage_exposure_hours_task,
)
from astrophotography.tests.factories import AstroImageFactory
from common.llm.providers import MockLLMProvider
from core.services import LandingPageTotalTimeSpentService
from core.tests.factories import LandingPageSettingsFactory


class TestLandingPageTotalTimeSpentService:
    @override_settings(LANDING_PAGE_TOTAL_TIME_SPENT_LLM_PROVIDER="mock")
    def test_create_default_uses_numeric_mock_response(self) -> None:
        service = LandingPageTotalTimeSpentService.create_default()

        result = service.parse_total_hours("<p>60x300s</p>")

        assert result == 0.0

    def test_parse_total_hours_returns_float(self) -> None:
        provider = MockLLMProvider()
        provider.configure(mock_response="1.5")

        service = LandingPageTotalTimeSpentService(provider=provider)

        result = service.parse_total_hours("<p>60x300s</p>")

        assert result == 1.5

    def test_parse_total_hours_returns_zero_for_empty_input(self) -> None:
        provider = MockLLMProvider()
        service = LandingPageTotalTimeSpentService(provider=provider)

        result = service.parse_total_hours("")

        assert result == 0.0

    def test_parse_total_hours_rejects_non_numeric_response(self) -> None:
        provider = MockLLMProvider()
        provider.configure(mock_response="one point five")

        service = LandingPageTotalTimeSpentService(provider=provider)

        with pytest.raises(ValueError, match="single number"):
            service.parse_total_hours("2h 30m")

    def test_prompt_instructs_llm_to_return_decimal_hours(self) -> None:
        provider = MockLLMProvider()
        service = LandingPageTotalTimeSpentService(provider=provider)

        prompt = service._build_system_prompt()

        assert "exact total in hours as a number" in prompt
        assert "exactly 2 digits after the decimal point" in prompt
        assert "convert every exposure to seconds first" in prompt
        assert "never double-count the same exposure description" in prompt
        assert "`30x180s` -> `30 * 180 = 5400s = 1.50`" in prompt
        assert "`Sky: 8 panels, 90s each + 15min Ha. Foreground: 3min`" in prompt
        assert (
            "10 × 120s = 20 min, 35 × 120s = 70 min, 10 × 180s = 30 min, 10 × 120s = 20 min"
            in prompt
        )
        assert "do not multiply `35 x 120s` by `10 panels`" in prompt
        assert "1.50" in prompt

    def test_parse_total_hours_rounds_to_two_decimals(self) -> None:
        provider = MockLLMProvider()
        provider.configure(mock_response="4.368888888888888")

        service = LandingPageTotalTimeSpentService(provider=provider)

        result = service.parse_total_hours("47x300s, 16x60s")

        assert result == 4.37


@pytest.mark.django_db
class TestLandingPageTotalTimeSpentTask:
    def test_calculate_task_updates_image_and_invalidates_cache(self, mocker) -> None:
        LandingPageSettingsFactory()
        mocker.patch(
            "astrophotography.models.calculate_astroimage_exposure_hours_task.delay_on_commit"
        )
        mock_invalidate_cache = mocker.patch(
            "astrophotography.tasks.CacheService.invalidate_landing_page_cache"
        )
        mock_invalidate_ssr = mocker.patch(
            "astrophotography.tasks.invalidate_frontend_ssr_cache_task.delay"
        )
        image = AstroImageFactory(exposure_details="60x300s", calculated_exposure_hours=0.0)
        mock_invalidate_cache.reset_mock()
        mock_invalidate_ssr.reset_mock()
        mocker.patch(
            "core.services.LandingPageTotalTimeSpentService.create_default",
            return_value=mocker.Mock(parse_total_hours=mocker.Mock(return_value=1.5)),
        )

        result = calculate_astroimage_exposure_hours_task(str(image.pk))

        image.refresh_from_db()
        assert image.calculated_exposure_hours == 1.5
        mock_invalidate_cache.assert_called_once_with()
        mock_invalidate_ssr.assert_called_once_with(["settings"])
        assert result == {
            "status": "success",
            "astro_image_id": str(image.pk),
            "parsed_hours": 1.5,
        }

    def test_calculate_task_returns_parsed_hours_when_settings_missing(self, mocker) -> None:
        mocker.patch(
            "astrophotography.models.calculate_astroimage_exposure_hours_task.delay_on_commit"
        )
        image = AstroImageFactory(exposure_details="2h total", calculated_exposure_hours=0.0)
        mocker.patch(
            "core.services.LandingPageTotalTimeSpentService.create_default",
            return_value=mocker.Mock(parse_total_hours=mocker.Mock(return_value=1.5)),
        )

        result = calculate_astroimage_exposure_hours_task(str(image.pk))

        assert result["parsed_hours"] == 1.5


@pytest.mark.django_db
class TestLandingPageTotalTimeSpentSignals:
    def test_astroimage_save_queues_task_with_exposure_details(self, mocker) -> None:
        mock_delay = mocker.patch(
            "astrophotography.models.calculate_astroimage_exposure_hours_task.delay_on_commit"
        )

        image = AstroImageFactory(exposure_details="2h total")

        mock_delay.assert_called_with(str(image.pk))

    def test_astroimage_save_skips_empty_exposure_details(self, mocker) -> None:
        mock_delay = mocker.patch(
            "astrophotography.models.calculate_astroimage_exposure_hours_task.delay_on_commit"
        )

        AstroImageFactory(exposure_details="")

        mock_delay.assert_not_called()

    def test_astroimage_save_does_not_queue_when_exposure_details_is_unchanged(
        self, mocker
    ) -> None:
        mock_delay = mocker.patch(
            "astrophotography.models.calculate_astroimage_exposure_hours_task.delay_on_commit"
        )
        image = AstroImageFactory(exposure_details="2h total")
        mock_delay.reset_mock()

        image.set_current_language("en")
        image.exposure_details = "2h total"
        image.save()

        mock_delay.assert_not_called()

    def test_astroimage_save_does_not_queue_when_only_other_field_changes(self, mocker) -> None:
        mock_delay = mocker.patch(
            "astrophotography.models.calculate_astroimage_exposure_hours_task.delay_on_commit"
        )
        image = AstroImageFactory(exposure_details="2h total")
        mock_delay.reset_mock()

        image.set_current_language("en")
        image.processing_details = "Updated processing details"
        image.save()

        mock_delay.assert_not_called()

    def test_astroimage_save_queues_when_exposure_details_changes(self, mocker) -> None:
        mock_delay = mocker.patch(
            "astrophotography.models.calculate_astroimage_exposure_hours_task.delay_on_commit"
        )
        image = AstroImageFactory(exposure_details="2h total")
        mock_delay.reset_mock()

        image.set_current_language("en")
        image.exposure_details = "3h total"
        image.save()

        mock_delay.assert_called_once_with(str(image.pk))

    def test_astroimage_save_for_non_default_language_does_not_queue(self, mocker) -> None:
        mock_delay = mocker.patch(
            "astrophotography.models.calculate_astroimage_exposure_hours_task.delay_on_commit"
        )
        image = AstroImageFactory(exposure_details="2h total")
        mock_delay.reset_mock()

        image.set_current_language("pl")
        image.exposure_details = "2h total"
        image.save()

        mock_delay.assert_not_called()

    def test_astroimage_delete_invalidates_settings_cache(self, mocker) -> None:
        mocker.patch(
            "astrophotography.models.calculate_astroimage_exposure_hours_task.delay_on_commit"
        )
        mock_invalidate_cache = mocker.patch(
            "astrophotography.signals.CacheService.invalidate_landing_page_cache"
        )
        mock_invalidate_ssr = mocker.patch(
            "astrophotography.signals.invalidate_frontend_ssr_cache_task.delay_on_commit"
        )
        image = AstroImageFactory(calculated_exposure_hours=1.5)
        mock_invalidate_cache.reset_mock()
        mock_invalidate_ssr.reset_mock()

        image.delete()

        mock_invalidate_cache.assert_called_once_with()
        assert mocker.call(["settings"]) in mock_invalidate_ssr.call_args_list

    def test_astroimage_save_invalidates_settings_when_calculated_exposure_hours_changes(
        self, mocker
    ) -> None:
        mocker.patch(
            "astrophotography.models.calculate_astroimage_exposure_hours_task.delay_on_commit"
        )
        mock_invalidate_cache = mocker.patch(
            "astrophotography.signals.CacheService.invalidate_landing_page_cache"
        )
        mock_invalidate_ssr = mocker.patch(
            "astrophotography.signals.invalidate_frontend_ssr_cache_task.delay_on_commit"
        )
        image = AstroImageFactory(calculated_exposure_hours=0.0)
        mock_invalidate_cache.reset_mock()
        mock_invalidate_ssr.reset_mock()

        image.calculated_exposure_hours = 1.5
        image.save(update_fields=["calculated_exposure_hours"])

        mock_invalidate_cache.assert_called_once_with()
        assert mocker.call(["settings"]) in mock_invalidate_ssr.call_args_list

    def test_astroimage_save_skips_settings_invalidation_when_calculated_exposure_hours_unchanged(
        self, mocker
    ) -> None:
        mocker.patch(
            "astrophotography.models.calculate_astroimage_exposure_hours_task.delay_on_commit"
        )
        mock_invalidate_cache = mocker.patch(
            "astrophotography.signals.CacheService.invalidate_landing_page_cache"
        )
        mock_invalidate_ssr = mocker.patch(
            "astrophotography.signals.invalidate_frontend_ssr_cache_task.delay_on_commit"
        )
        image = AstroImageFactory(calculated_exposure_hours=1.5)
        mock_invalidate_cache.reset_mock()
        mock_invalidate_ssr.reset_mock()

        image.slug = "updated-slug"
        image.save(update_fields=["slug"])

        mock_invalidate_cache.assert_not_called()
        assert mocker.call(["settings"]) not in mock_invalidate_ssr.call_args_list


@pytest.mark.django_db
class TestLandingPageTotalTimeSpentCommand:
    def test_command_calculates_only_images_without_hours_by_default(self, mocker) -> None:
        LandingPageSettingsFactory()
        mocker.patch(
            "astrophotography.models.calculate_astroimage_exposure_hours_task.delay_on_commit"
        )
        first = AstroImageFactory(exposure_details="first", calculated_exposure_hours=0.0)
        second = AstroImageFactory(exposure_details="second", calculated_exposure_hours=7.0)
        type(second).objects.filter(pk=second.pk).update(calculated_exposure_hours=7.0)
        mock_calculate_task = mocker.patch(
            "core.management.commands.recalculate_landing_page_total_time_spent."
            "calculate_astroimage_exposure_hours_task",
            side_effect=lambda astro_image_id: (
                type(first).objects.filter(pk=astro_image_id).update(calculated_exposure_hours=1.5),
                {
                    "status": "success",
                    "astro_image_id": astro_image_id,
                    "parsed_hours": 1.5,
                },
            )[1],
        )
        mock_invalidate_cache = mocker.patch(
            "core.management.commands.recalculate_landing_page_total_time_spent."
            "CacheService.invalidate_landing_page_cache"
        )
        mock_invalidate_ssr = mocker.patch(
            "core.management.commands.recalculate_landing_page_total_time_spent."
            "invalidate_frontend_ssr_cache_task.delay"
        )
        output = StringIO()

        call_command("recalculate_landing_page_total_time_spent", stdout=output)

        first.refresh_from_db()
        assert first.calculated_exposure_hours == 1.5
        mock_calculate_task.assert_called_once_with(str(first.pk))
        mock_invalidate_cache.assert_called_once_with()
        mock_invalidate_ssr.assert_called_once_with(["settings"])
        assert "8.5h" in output.getvalue()
        assert "Calculated total time spent" in output.getvalue()

    def test_command_recalculates_all_images_with_flag(self, mocker) -> None:
        LandingPageSettingsFactory()
        mocker.patch(
            "astrophotography.models.calculate_astroimage_exposure_hours_task.delay_on_commit"
        )
        first = AstroImageFactory(exposure_details="first", calculated_exposure_hours=1.0)
        second = AstroImageFactory(exposure_details="second", calculated_exposure_hours=7.0)
        type(first).objects.filter(pk=first.pk).update(calculated_exposure_hours=1.0)
        type(second).objects.filter(pk=second.pk).update(calculated_exposure_hours=7.0)
        mapping = {
            str(first.pk): 1.5,
            str(second.pk): 7.0,
        }
        mock_calculate_task = mocker.patch(
            "core.management.commands.recalculate_landing_page_total_time_spent."
            "calculate_astroimage_exposure_hours_task",
            side_effect=lambda astro_image_id: (
                type(first)
                .objects.filter(pk=astro_image_id)
                .update(calculated_exposure_hours=mapping[astro_image_id]),
                {
                    "status": "success",
                    "astro_image_id": astro_image_id,
                    "parsed_hours": mapping[astro_image_id],
                },
            )[1],
        )
        mock_invalidate_cache = mocker.patch(
            "core.management.commands.recalculate_landing_page_total_time_spent."
            "CacheService.invalidate_landing_page_cache"
        )
        mock_invalidate_ssr = mocker.patch(
            "core.management.commands.recalculate_landing_page_total_time_spent."
            "invalidate_frontend_ssr_cache_task.delay"
        )
        output = StringIO()

        call_command("recalculate_landing_page_total_time_spent", "--recalculate", stdout=output)

        first.refresh_from_db()
        second.refresh_from_db()
        assert first.calculated_exposure_hours == 1.5
        assert second.calculated_exposure_hours == 7.0
        assert mock_calculate_task.call_count == 2
        mock_invalidate_cache.assert_called_once_with()
        mock_invalidate_ssr.assert_called_once_with(["settings"])
        assert "8.5h" in output.getvalue()
        assert "Rebuilt total time spent" in output.getvalue()


@pytest.mark.django_db
class TestLandingPageTotalTimeSpentApi:
    def test_settings_serializer_rounds_total_time_spent(self, api_client, mocker) -> None:
        mocker.patch(
            "astrophotography.models.calculate_astroimage_exposure_hours_task.delay_on_commit"
        )
        LandingPageSettingsFactory()
        image = AstroImageFactory(calculated_exposure_hours=1.5)
        type(image).objects.filter(pk=image.pk).update(calculated_exposure_hours=1.5)

        response = api_client.get("/v1/settings/")

        assert response.status_code == 200
        assert response.data["total_time_spent"] == 4
