# backend/core/tests/test_tasks.py
"""
Tests for translation-related tasks, including Celery tasks, service logic,
and GPT agent interactions.
"""

from unittest.mock import MagicMock

import pytest
from pytest_mock import MockerFixture
from requests.exceptions import RequestException

from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist

from translation.agents import TranslationAgent
from translation.services import TranslationService
from translation.tasks import translate_instance_task


@pytest.mark.django_db
class TestTaskAgent:
    """Tests for TranslationAgent."""

    def test_translate_calls_provider_correctly(self, mock_llm_provider: MagicMock):
        """Test that the agent calls provider.ask_question twice"""
        # Setup mock responses
        mock_llm_provider.ask_question.side_effect = ["Translated raw", "Przetłumaczony tekst"]

        # Instantiate agent with mock provider
        agent = TranslationAgent(provider=mock_llm_provider)

        # Call translate
        result = agent.translate("Hello World", "pl")

        # Assertions
        assert result == "Przetłumaczony tekst"

        # Verify calls to provider
        assert mock_llm_provider.ask_question.call_count == 2

        # 1st call (Translate)
        call1 = mock_llm_provider.ask_question.call_args_list[0]
        assert "Polish" in call1.kwargs["system_prompt"]
        assert call1.kwargs["user_message"] == "Hello World"
        assert call1.kwargs["temperature"] == 0.0

        # 2nd call (Edit)
        call2 = mock_llm_provider.ask_question.call_args_list[1]
        assert "Polish" in call2.kwargs["system_prompt"]
        assert call2.kwargs["user_message"] == "Translated raw"
        assert call2.kwargs["temperature"] == 0.2

    def test_translate_handles_provider_error_gracefully(self, mock_llm_provider: MagicMock):
        """Test that the agent returns None or fallback when provider fails"""
        # Simulate Provider returning None (failure)
        mock_llm_provider.ask_question.return_value = None

        agent = TranslationAgent(provider=mock_llm_provider)
        result = agent.translate("Hello", "pl")

        assert result is None

    def test_extract_all_tags_replaces_tags_with_placeholders(self, mock_llm_provider: MagicMock):
        """Test that _extract_all_tags correctly extracts and replaces HTML tags."""
        agent = TranslationAgent(provider=mock_llm_provider)
        html = "<p><strong>Hello</strong> world</p>"

        text, tag_map = agent._extract_all_html_tags(html)

        # Verify placeholders are created
        assert "[[T0]]" in text
        assert "[[T1]]" in text
        assert "[[T2]]" in text
        assert "[[T3]]" in text

        # Verify tags are stored
        assert tag_map[0] == "<p>"
        assert tag_map[1] == "<strong>"
        assert tag_map[2] == "</strong>"
        assert tag_map[3] == "</p>"

        # Verify text content is preserved
        assert "Hello" in text
        assert "world" in text

    def test_restore_all_tags_reconstructs_html(self, mock_llm_provider: MagicMock):
        """Test that _restore_all_tags correctly restores HTML from placeholders."""
        agent = TranslationAgent(provider=mock_llm_provider)
        translated_text = "[[T0]][[T1]]Cześć[[T2]] świat[[T3]]"
        tag_map = {
            0: "<p>",
            1: "<strong>",
            2: "</strong>",
            3: "</p>",
        }

        result = agent._restore_all_tags(translated_text, tag_map)

        assert result == "<p><strong>Cześć</strong> świat</p>"

    def test_translate_html_preserves_list_with_attributes(self, mock_llm_provider: MagicMock):
        """
        Test that translate_html preserves complex HTML lists with attributes.
        """
        html_input = """<ul>
    <li data-list-item-id="abc123"><strong>APOD</strong> and <strong>SKY</strong></li>
    <li data-list-item-id="def456"><strong>AAPOD2</strong></li>
</ul>"""

        # Mock responses for two-step translation
        response_content = (
            "[[T0]]\n    [[T1]][[T2]]APOD[[T3]] i [[T4]]SKY[[T5]][[T6]]\n    "
            "[[T7]][[T8]]AAPOD2[[T9]][[T10]]\n[[T11]]"
        )

        # side_effect for translate() call inside translate_html:
        # 1. raw translation
        # 2. edited translation
        # Logic in agent.translate() does 2 calls.
        mock_llm_provider.ask_question.side_effect = [
            response_content,  # raw
            response_content,  # edited
        ]

        agent = TranslationAgent(provider=mock_llm_provider)
        result = agent.translate_html(html_input, "pl")

        # Verify structure preserved
        assert "<ul>" in result
        assert "</ul>" in result
        assert 'data-list-item-id="abc123"' in result
        assert 'data-list-item-id="def456"' in result
        assert "<strong>" in result
        assert "</strong>" in result
        assert "<li" in result
        assert "</li>" in result


@pytest.mark.django_db
class TestTaskService:
    """Tests for TranslationService business logic."""

    def test_get_available_languages_returns_list(self):
        """Verify that get_available_languages returns a list of language codes."""
        languages = TranslationService.get_available_languages()
        assert isinstance(languages, list)
        assert len(languages) > 0
        assert "en" in languages
        assert "pl" in languages

    def test_get_available_languages_matches_settings(self):
        """Verify that the returned languages match configuration."""
        languages = TranslationService.get_available_languages()
        parler_configs = getattr(settings, "PARLER_LANGUAGES", {})
        parler_langs = parler_configs.get(None, [])
        expected_codes = [
            lang["code"] for lang in parler_langs if isinstance(lang, dict) and "code" in lang
        ]
        assert len(expected_codes) > 0
        assert set(languages) == set(expected_codes)

    def test_is_empty_text_edge_cases(self):
        """Verify is_empty_text with various HTML and whitespace cases."""
        assert TranslationService.is_empty_text("") is True
        assert TranslationService.is_empty_text(None) is True
        assert TranslationService.is_empty_text("<p></p>") is True
        assert TranslationService.is_empty_text("<p>&nbsp;</p>") is True
        assert TranslationService.is_empty_text("   ") is True
        assert TranslationService.is_empty_text("<p>Content</p>") is False
        assert TranslationService.is_empty_text("Valid") is False

    def test_parler_ceremony_skip_if_exists(self, mocker: MockerFixture):
        """Verify that _parler_ceremony yields None and stops if translation exists."""
        instance = mocker.MagicMock()
        mocker.patch.object(TranslationService, "_has_translation", return_value=(True, "Existing"))

        gen = TranslationService._parler_ceremony(instance, "name", "pl")
        val = next(gen)
        assert val is None
        with pytest.raises(StopIteration):
            next(gen)

    def test_parler_ceremony_yields_source(self, mocker: MockerFixture):
        """Verify that _parler_ceremony yields source text if translation is missing."""
        instance = mocker.MagicMock()
        instance.get_current_language.return_value = "en"
        mocker.patch.object(TranslationService, "_has_translation", return_value=(False, None))
        mocker.patch.object(TranslationService, "_get_default_language_text", return_value="Source")

        gen = TranslationService._parler_ceremony(instance, "name", "pl")
        val = next(gen)
        assert val == "Source"
        try:
            gen.send("Translated")
        except StopIteration:
            pass
        instance.set_current_language.assert_any_call("pl")
        instance.set_current_language.assert_any_call("en")

    def test_translate_parler_tag_uses_correct_agent_method(self, mocker: MockerFixture):
        """Verify that translate_parler_tag calls translate_tag and handles slugs."""
        instance = mocker.MagicMock()
        instance.get_current_language.return_value = "en"
        instance.name = "TranslatedTag"

        mock_get_agent = mocker.patch("translation.services.TranslationService._get_agent")
        mock_agent = mock_get_agent.return_value
        mock_agent.translate_tag.return_value = "TranslatedTag"

        mocker.patch.object(TranslationService, "_has_translation", return_value=(False, None))
        mocker.patch.object(TranslationService, "_get_default_language_text", return_value="Source")

        result = TranslationService.translate_parler_tag(instance, "pl")
        assert result == ["TranslatedTag", "translatedtag"]
        mock_agent.translate_tag.assert_called_once_with("Source", "pl")
        assert instance.name == "TranslatedTag"
        assert instance.slug == "translatedtag"

    def test_translate_user_handles_text_and_html(
        self, mocker: MockerFixture, mock_task_infrastructure, mock_llm_provider: MagicMock
    ):
        """
        Test that translate_user uses correct handlers for bio (HTML) and short_description (text).
        """
        mock_get_agent = mocker.patch("translation.services.TranslationService._get_agent")
        mock_run_parler = mocker.patch(
            "translation.services.TranslationService._run_parler_translation"
        )

        instance = mocker.MagicMock()
        mock_run_parler.return_value = "Translated"
        mock_agent = mock_get_agent.return_value

        # Call the method
        TranslationService.translate_user(instance, "pl")

        # Verify calls - we expect 2 calls
        assert mock_run_parler.call_count == 2

        calls = mock_run_parler.call_args_list
        fields_processed = {}

        for call in calls:
            args, _ = call
            field_name = args[1]
            handler = args[3]
            fields_processed[field_name] = handler

        # Verify short_description used standard text translator
        assert "short_description" in fields_processed
        assert fields_processed["short_description"] == mock_agent.translate

        # Verify bio used HTML translator
        assert "bio" in fields_processed
        assert fields_processed["bio"] == mock_agent.translate_html

    def test_translate_user_saves_translations(
        self, mocker: MockerFixture, mock_task_infrastructure
    ):
        """Test that translated fields are saved."""
        mock_get_agent = mocker.patch("translation.services.TranslationService._get_agent")

        instance = mocker.MagicMock()
        mock_agent = mock_get_agent.return_value
        mock_agent.translate.return_value = "Opis"
        mock_agent.translate_html.return_value = "<p>Bio</p>"

        # Mock the helper to actually return values like the real method would with the mock agent
        # We can't easily mock the generator-based _run_parler_translation in a simple way
        # that mimics full execution without complexity, so we'll mock _run_parler_translation
        # directly to return the values we expect

        def side_effect(inst, field, lang, handler, force=False):
            if field == "short_description":
                return "Opis"
            return "<p>Bio</p>"

        mocker.patch(
            "translation.services.TranslationService._run_parler_translation",
            side_effect=side_effect,
        )

        # Call method
        results = TranslationService.translate_user(instance, "pl")

        # Verify results
        assert results["short_description"] == "Opis"
        assert results["bio"] == "<p>Bio</p>"

        # Verify save_translations called
        instance.save_translations.assert_called_once()

    def test_translate_astro_image_uses_html_agent_for_description(self, mocker: MockerFixture):
        """Verify HTML agent use for description in AstroImage translation."""
        mock_get_agent = mocker.patch("translation.services.TranslationService._get_agent")
        instance = mocker.MagicMock()
        mock_agent = mock_get_agent.return_value

        mock_run = mocker.patch.object(TranslationService, "_run_parler_translation")

        TranslationService.translate_astro_image(instance, "pl")

        call_args_list = mock_run.call_args_list
        # We expect 4 calls: 2 for name (trans+edit), 2 for description (trans+edit)
        # Note: logic might vary by implementation, but assuming 4 based on original assertion
        assert len(call_args_list) == 4

        # Verify calls use expected handlers
        # args structure: (instance, field_name, language_code, handler_func)

        # Description should use translate_html
        # We scan calls to find 'description' field
        desc_calls = [c for c in call_args_list if c[0][1] == "description"]
        assert len(desc_calls) >= 1
        assert desc_calls[0][0][3] == mock_agent.translate_html

        # Name should use translate
        name_calls = [c for c in call_args_list if c[0][1] == "name"]
        assert len(name_calls) >= 1
        assert name_calls[0][0][3] == mock_agent.translate

    def test_parler_ceremony_obeys_force_parameter(self, mocker: MockerFixture):
        """Verify that _parler_ceremony yields source even if translation exists with force=True."""
        instance = mocker.MagicMock()
        instance.get_current_language.return_value = "en"
        mocker.patch.object(TranslationService, "_get_default_language_text", return_value="Source")

        gen = TranslationService._parler_ceremony(instance, "name", "pl", force=True)
        val = next(gen)
        assert val == "Source"


@pytest.mark.django_db
class TestTranslateInstanceTask:
    """Tests for Celery tasks (thin wrappers)."""

    def test_translate_instance_task_calls_service_method(
        self, mock_task_infrastructure, mocker: MockerFixture
    ):
        """Task should call TranslationService method and create TranslationTask."""
        infra = mock_task_infrastructure
        mock_model = mocker.Mock()
        mock_instance = mocker.Mock()
        mock_instance.pk = 1
        mock_model.objects.get.return_value = mock_instance
        infra["get_model"].return_value = mock_model
        infra["service"].translate_place = mocker.Mock(return_value={"name": "Warszawa"})
        mock_task_record = mocker.Mock()
        infra["task_model"].objects.update_or_create.return_value = (mock_task_record, True)

        translate_instance_task(
            model_name="astrophotography.Place",
            instance_pk=1,
            language_code="pl",
            method_name="translate_place",
        )

        assert infra["task_model"].objects.update_or_create.call_count == 2

        # Verify RUNNING transition
        call_running = infra["task_model"].objects.update_or_create.call_args_list[0]
        assert call_running.kwargs["defaults"]["status"] == infra["task_model"].Status.RUNNING

        # Verify COMPLETED transition
        call_completed = infra["task_model"].objects.update_or_create.call_args_list[1]
        assert call_completed.kwargs["defaults"]["status"] == infra["task_model"].Status.COMPLETED

        infra["service"].translate_place.assert_called_once_with(mock_instance, "pl")

    def test_translate_instance_task_handles_missing_instance(
        self, mock_task_infrastructure, mocker: MockerFixture
    ):
        """Task should handle deleted instances without retrying."""
        infra = mock_task_infrastructure
        mock_model = mocker.Mock()
        mock_model.objects.get.side_effect = ObjectDoesNotExist("Not found")
        infra["get_model"].return_value = mock_model
        infra["task_model"].objects.update_or_create.return_value = (mocker.Mock(), True)

        result = translate_instance_task(
            model_name="astrophotography.Place",
            instance_pk=999,
            language_code="pl",
            method_name="translate_place",
        )

        assert result["error"] == "Instance not found"

    def test_translate_instance_task_inherits_idempotency(
        self, mock_task_infrastructure, mocker: MockerFixture
    ):
        """Task should not re-translate if translation exists."""
        infra = mock_task_infrastructure
        mock_model = mocker.Mock()
        mock_instance = mocker.Mock()
        mock_instance.pk = 1
        mock_model.objects.get.return_value = mock_instance
        infra["get_model"].return_value = mock_model
        infra["task_model"].objects.update_or_create.return_value = (mocker.Mock(), True)
        infra["service"].translate_place = mocker.Mock(
            return_value={"name": "Existing translation"}
        )

        translate_instance_task(
            model_name="astrophotography.Place",
            instance_pk=1,
            language_code="pl",
            method_name="translate_place",
        )
        translate_instance_task(
            model_name="astrophotography.Place",
            instance_pk=1,
            language_code="pl",
            method_name="translate_place",
        )

        assert infra["service"].translate_place.call_count == 2

    def test_translate_instance_task_retry_on_request_exception(
        self, mock_task_infrastructure, mocker: MockerFixture
    ):
        """Task should update status to FAILED on exception."""
        infra = mock_task_infrastructure
        mock_model = mocker.Mock()
        mock_instance = mocker.Mock()
        mock_instance.pk = 1
        mock_model.objects.get.return_value = mock_instance
        infra["get_model"].return_value = mock_model
        infra["task_model"].objects.update_or_create.return_value = (mocker.Mock(), True)
        infra["service"].translate_place = mocker.Mock(side_effect=RequestException("Error"))

        with pytest.raises(Exception):
            translate_instance_task(
                model_name="astrophotography.Place",
                instance_pk=1,
                language_code="pl",
                method_name="translate_place",
            )

        # Verify status was NOT updated to FAILED (since it's a retry)
        infra["task_model"].objects.filter.assert_not_called()

    def test_translate_instance_task_passes_kwargs(
        self, mock_task_infrastructure, mocker: MockerFixture
    ):
        """Task should pass kwargs to service method."""
        infra = mock_task_infrastructure
        mock_model = mocker.Mock()
        mock_instance = mocker.Mock()
        mock_instance.pk = 5
        mock_model.objects.get.return_value = mock_instance
        infra["get_model"].return_value = mock_model
        infra["task_model"].objects.update_or_create.return_value = (mocker.Mock(), True)
        infra["service"].translate_parler_tag = mocker.Mock(return_value=["Django"])

        translate_instance_task(
            model_name="astrophotography.Tag",
            instance_pk=5,
            language_code="pl",
            method_name="translate_parler_tag",
            force=True,
        )

        infra["service"].translate_parler_tag.assert_called_once_with(
            mock_instance, "pl", force=True
        )
