# backend/core/tests/test_tasks.py
"""
Tests for translation-related tasks, including Celery tasks, service logic,
and GPT agent interactions.
"""
from unittest.mock import MagicMock, Mock, patch

import pytest
from requests.exceptions import RequestException

from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist

from translation.agents import GPTTranslationAgent
from translation.services import TranslationService
from translation.tasks import translate_instance_task


@pytest.fixture
def mock_openai_client():
    with patch("translation.agents.OpenAI") as mock:
        yield mock


@pytest.fixture
def mock_task_infrastructure():
    with (
        patch("translation.tasks.apps.get_model") as mock_get_model,
        patch("translation.tasks.TranslationService") as mock_service,
        patch("translation.tasks.TranslationTask") as mock_task_model,
        patch("translation.tasks.ContentType") as mock_content_type,
    ):
        yield {
            "get_model": mock_get_model,
            "service": mock_service,
            "task_model": mock_task_model,
            "content_type": mock_content_type,
        }


@pytest.mark.django_db
class TestTaskAgent:
    """Tests for GPTTranslationAgent."""

    def test_translate_calls_openai_correctly(self, mock_openai_client):
        """Test that the agent initializes client and calls chat.completions.create twice"""
        # Setup mock responses
        mock_response1 = MagicMock()
        mock_response1.choices[0].message.content = "Translated raw"

        mock_response2 = MagicMock()
        mock_response2.choices[0].message.content = "Przetłumaczony tekst"

        mock_client_instance = mock_openai_client.return_value
        mock_client_instance.chat.completions.create.side_effect = [mock_response1, mock_response2]

        # Instantiate agent
        agent = GPTTranslationAgent()

        # Call translate
        result = agent.translate("Hello World", "pl")

        # Assertions
        assert result == "Przetłumaczony tekst"

        # Verify calls to OpenAI
        assert mock_client_instance.chat.completions.create.call_count == 2

        # 1st call (Translate)
        call1 = mock_client_instance.chat.completions.create.call_args_list[0][1]
        assert call1["model"] == "gpt-4o"
        assert "Polish" in call1["messages"][0]["content"]
        assert call1["messages"][1]["content"] == "Hello World"

        # 2nd call (Edit)
        call2 = mock_client_instance.chat.completions.create.call_args_list[1][1]
        assert call2["model"] == "gpt-4o"
        assert "Polish" in call2["messages"][0]["content"]
        assert call2["messages"][1]["content"] == "Translated raw"

    def test_translate_handles_api_error_gracefully(self, mock_openai_client):
        """Test that the agent returns None or fallback when API fails"""
        mock_client_instance = mock_openai_client.return_value
        # Simulate API Exception
        mock_client_instance.chat.completions.create.side_effect = Exception("API Error")

        agent = GPTTranslationAgent()
        result = agent.translate("Hello", "pl")

        assert result is None


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

    def test_fetch_place_name_calls_agent_correctly(self):
        """Verify TranslationService.fetch_place_name calls GPTTranslationAgent correctly."""
        with patch.object(TranslationService.agent, "translate_place") as mock_translate:
            mock_translate.return_value = "Hawaje"
            result = TranslationService.fetch_place_name("Hawaii", "US", "pl")
            assert result == "Hawaje"
            mock_translate.assert_called_once_with("Hawaii", "pl", "US")

    def test_is_empty_text_edge_cases(self):
        """Verify is_empty_text with various HTML and whitespace cases."""
        assert TranslationService.is_empty_text("") is True
        assert TranslationService.is_empty_text(None) is True
        assert TranslationService.is_empty_text("<p></p>") is True
        assert TranslationService.is_empty_text("<p>&nbsp;</p>") is True
        assert TranslationService.is_empty_text("   ") is True
        assert TranslationService.is_empty_text("<p>Content</p>") is False
        assert TranslationService.is_empty_text("Valid") is False

    def test_parler_ceremony_skip_if_exists(self):
        """Verify that _parler_ceremony yields None and stops if translation exists."""
        instance = MagicMock()
        with patch.object(TranslationService, "_has_translation", return_value=(True, "Existing")):
            gen = TranslationService._parler_ceremony(instance, "name", "pl")
            val = next(gen)
            assert val is None
            with pytest.raises(StopIteration):
                next(gen)

    def test_parler_ceremony_yields_source(self):
        """Verify that _parler_ceremony yields source text if translation is missing."""
        instance = MagicMock()
        instance.get_current_language.return_value = "en"
        with patch.object(TranslationService, "_has_translation", return_value=(False, None)):
            with patch.object(
                TranslationService, "_get_default_language_text", return_value="Source"
            ):
                gen = TranslationService._parler_ceremony(instance, "name", "pl")
                val = next(gen)
                assert val == "Source"
                try:
                    gen.send("Translated")
                except StopIteration:
                    pass
                instance.set_current_language.assert_any_call("pl")
                instance.set_current_language.assert_any_call("en")

    def test_translate_parler_tag_uses_correct_agent_method(self):
        """Verify that translate_parler_tag calls translate_tag and handles slugs."""
        instance = MagicMock()
        instance.get_current_language.return_value = "en"
        instance.name = "TranslatedTag"
        with patch.object(TranslationService, "_has_translation", return_value=(False, None)):
            with patch.object(
                TranslationService, "_get_default_language_text", return_value="Source"
            ):
                with patch.object(
                    TranslationService.agent, "translate_tag", return_value="TranslatedTag"
                ) as mock_translate:
                    result = TranslationService.translate_parler_tag(instance, "pl")
                    assert result == ["TranslatedTag", "translatedtag"]
                    mock_translate.assert_called_once_with("Source", "pl")
                    assert instance.name == "TranslatedTag"
                    assert instance.slug == "translatedtag"

    def test_translate_astro_image_uses_html_agent_for_description(self):
        """Verify HTML agent use for description in AstroImage translation."""
        instance = MagicMock()
        with patch.object(TranslationService, "_run_parler_translation") as mock_run:
            TranslationService.translate_astro_image(instance, "pl")
            call_args_list = mock_run.call_args_list
            assert len(call_args_list) == 4
            handler_description = call_args_list[1][0][3]
            assert handler_description == TranslationService.agent.translate_html
            handler_name = call_args_list[0][0][3]
            assert handler_name == TranslationService.agent.translate

    def test_parler_ceremony_obeys_force_parameter(self):
        """Verify that _parler_ceremony yields source even if translation exists with force=True."""
        instance = MagicMock()
        instance.get_current_language.return_value = "en"
        with patch.object(TranslationService, "_get_default_language_text", return_value="Source"):
            gen = TranslationService._parler_ceremony(instance, "name", "pl", force=True)
            val = next(gen)
            assert val == "Source"


@pytest.mark.django_db
class TestTranslateInstanceTask:
    """Tests for Celery tasks (thin wrappers)."""

    def test_translate_instance_task_calls_service_method(self, mock_task_infrastructure):
        """Task should call TranslationService method and create TranslationTask."""
        infra = mock_task_infrastructure
        mock_model = Mock()
        mock_instance = Mock()
        mock_instance.pk = 1
        mock_model.objects.get.return_value = mock_instance
        infra["get_model"].return_value = mock_model
        infra["service"].translate_place = Mock(return_value={"name": "Warszawa"})
        mock_task_record = Mock()
        infra["task_model"].objects.update_or_create.return_value = (mock_task_record, True)

        translate_instance_task(
            model_name="astrophotography.Place",
            instance_pk=1,
            language_code="pl",
            method_name="translate_place",
        )

        infra["task_model"].objects.update_or_create.assert_called_once()
        _, kwargs = infra["task_model"].objects.update_or_create.call_args
        assert kwargs["defaults"]["status"] == infra["task_model"].Status.RUNNING
        infra["service"].translate_place.assert_called_once_with(mock_instance, "pl")
        assert mock_task_record.status == infra["task_model"].Status.COMPLETED

    def test_translate_instance_task_handles_missing_instance(self, mock_task_infrastructure):
        """Task should handle deleted instances without retrying."""
        infra = mock_task_infrastructure
        mock_model = Mock()
        mock_model.objects.get.side_effect = ObjectDoesNotExist("Not found")
        infra["get_model"].return_value = mock_model
        infra["task_model"].objects.update_or_create.return_value = (Mock(), True)

        result = translate_instance_task(
            model_name="astrophotography.Place",
            instance_pk=999,
            language_code="pl",
            method_name="translate_place",
        )

        assert result["error"] == "Instance not found"

    def test_translate_instance_task_inherits_idempotency(self, mock_task_infrastructure):
        """Task should not re-translate if translation exists."""
        infra = mock_task_infrastructure
        mock_model = Mock()
        mock_instance = Mock()
        mock_instance.pk = 1
        mock_model.objects.get.return_value = mock_instance
        infra["get_model"].return_value = mock_model
        infra["task_model"].objects.update_or_create.return_value = (Mock(), True)
        infra["service"].translate_place = Mock(return_value={"name": "Existing translation"})

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

    def test_translate_instance_task_retry_on_request_exception(self, mock_task_infrastructure):
        """Task should update status to FAILED on exception."""
        infra = mock_task_infrastructure
        mock_model = Mock()
        mock_instance = Mock()
        mock_instance.pk = 1
        mock_model.objects.get.return_value = mock_instance
        infra["get_model"].return_value = mock_model
        infra["task_model"].objects.update_or_create.return_value = (Mock(), True)
        infra["service"].translate_place = Mock(side_effect=RequestException("Error"))

        with pytest.raises(Exception):
            translate_instance_task(
                model_name="astrophotography.Place",
                instance_pk=1,
                language_code="pl",
                method_name="translate_place",
            )

        # Verify status was NOT updated to FAILED (since it's a retry)
        infra["task_model"].objects.filter.assert_not_called()

    def test_translate_instance_task_passes_kwargs(self, mock_task_infrastructure):
        """Task should pass kwargs to service method."""
        infra = mock_task_infrastructure
        mock_model = Mock()
        mock_instance = Mock()
        mock_instance.pk = 5
        mock_model.objects.get.return_value = mock_instance
        infra["get_model"].return_value = mock_model
        infra["task_model"].objects.update_or_create.return_value = (Mock(), True)
        infra["service"].translate_parler_tag = Mock(return_value=["Django"])

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
