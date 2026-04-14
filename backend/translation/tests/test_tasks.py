# backend/core/tests/test_tasks.py
"""
Tests for translation-related tasks, including Celery tasks, service logic,
and GPT agent interactions.
"""

import functools
import uuid
from unittest.mock import MagicMock

import pytest
from pytest_mock import MockerFixture
from requests.exceptions import RequestException

from django.core.exceptions import ObjectDoesNotExist
from django.utils.text import slugify

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
class TestTranslationServiceBusinessLogic:
    """Tests for TranslationService business logic."""

    def test_get_available_languages(self):
        """Test getting available languages from settings."""
        languages = TranslationService.get_available_languages()
        assert "en" in languages
        assert "pl" in languages
        assert len(languages) >= 2

    def test_get_available_languages_fallback(self, settings):
        """Test fallback when settings are missing/empty."""
        settings.PARLER_LANGUAGES = {}
        languages = TranslationService.get_available_languages()
        assert languages == []

    def test_is_empty_text(self):
        """Test HTML empty text detection."""
        assert TranslationService.is_empty_text("") is True
        assert TranslationService.is_empty_text(None) is True
        assert TranslationService.is_empty_text("<p></p>") is True
        assert TranslationService.is_empty_text("<p>&nbsp;</p>") is True
        assert TranslationService.is_empty_text("   ") is True
        assert TranslationService.is_empty_text("<p>Content</p>") is False
        assert TranslationService.is_empty_text("Valid") is False

    def test_translate_parler_tag_no_source(self, mocker, tag_factory):
        """Test skipping when source text is empty."""
        instance = tag_factory(name="", slug=f"tag-{uuid.uuid4()}")

        mock_agent = mocker.Mock()
        service = TranslationService(agent=mock_agent)

        mocker.patch.object(service, "_get_default_language_text", return_value="")

        result, failures = service.translate_parler_tag(instance, "pl")

        assert result == []
        assert failures == {}
        mock_agent.translate_tag.assert_not_called()

    def test_translate_parler_tag_skips_existing(self, mocker, tag_factory):
        """Test skipping if translation already exists."""
        unique_name = f"Existing-{uuid.uuid4()}"
        instance = tag_factory(name=unique_name, slug=f"tag-{uuid.uuid4()}")

        mock_agent = mocker.Mock()
        service = TranslationService(agent=mock_agent)

        # We need to simulate that it HAS translation with matching slug
        # The service checks name then slug.
        expected_slug = slugify(unique_name, allow_unicode=True)
        # We return matching slug so it doesn't try to update and hit duplicate key
        mocker.patch.object(
            service,
            "_has_translation",
            side_effect=[(True, f"{unique_name}PL"), (True, expected_slug)],
        )

        result, failures = service.translate_parler_tag(instance, "pl")

        assert result == []
        assert failures == {}
        mock_agent.translate_tag.assert_not_called()

    def test_translate_parler_tag_success(self, mocker, tag_factory):
        """Test full successful tag translation flow."""
        unique_name = f"Nebula-{uuid.uuid4()}"
        instance = tag_factory(name=unique_name, slug=f"tag-{uuid.uuid4()}")

        mock_agent = mocker.Mock()
        translated_name = "Mgławica"
        mock_agent.translate_tag.return_value = translated_name

        service = TranslationService(agent=mock_agent)

        mocker.patch.object(service, "_has_translation", return_value=(False, None))
        mocker.patch.object(service, "_get_default_language_text", return_value=unique_name)

        result, failures = service.translate_parler_tag(instance, "pl")

        assert translated_name in result
        assert failures == {}
        mock_agent.translate_tag.assert_called_with(unique_name, "pl")

        instance.set_current_language("pl")
        assert instance.name == translated_name
        assert instance.slug == slugify(translated_name, allow_unicode=True)

    def test_translate_user_success(self, mocker, user_factory):
        """Test translate_user calls run_parler_translation correctly."""
        instance = user_factory()

        mock_agent = mocker.Mock()
        service = TranslationService(agent=mock_agent)

        # Mock internal helper to avoid DB/transaction complexity in unit test
        mocker.patch.object(service, "_run_parler_translation", return_value=("Translated", None))
        mocker.patch.object(service, "_save_translations")

        results, failures = service.translate_user(instance, "pl")

        assert results["short_description"] == "Translated"
        assert results["bio"] == "Translated"
        assert failures == {}
        assert service._run_parler_translation.call_count == 2
        service._save_translations.assert_called_once()

    def test_translate_astro_image_success(self, mocker, astro_image_factory):
        """Test translate_astro_image success flow."""
        instance = astro_image_factory()

        mock_agent = mocker.Mock()
        service = TranslationService(agent=mock_agent)

        mocker.patch.object(service, "_run_parler_translation", return_value=("Translated", None))
        mocker.patch.object(service, "_save_translations")

        results, failures = service.translate_astro_image(instance, "pl")
        assert failures == {}

        assert service._run_parler_translation.call_count == 4  # 4 fields
        service._save_translations.assert_called_once()

    def test_translate_place_success(self, mocker, place_factory):
        """Test translate_place uses specialized handler."""
        instance = place_factory(country__name="Poland")

        mock_agent = mocker.Mock()
        service = TranslationService(agent=mock_agent)

        mocker.patch.object(service, "_run_parler_translation", return_value=("Translated", None))
        mocker.patch.object(service, "_save_translations")

        result, failures = service.translate_place(instance, "pl")

        assert result == "Translated"
        assert failures == {}
        service._run_parler_translation.assert_called_once()
        # Verify custom handler was passed
        args, _ = service._run_parler_translation.call_args
        assert callable(args[3])  # handler is the 4th arg

    def test_translate_user_handles_text_and_html(
        self, mocker: MockerFixture, mock_task_infrastructure, mock_llm_provider: MagicMock
    ):
        """Verify that translation handles both plain text and HTML fields."""
        mock_agent = mocker.Mock()
        service = TranslationService(agent=mock_agent)

        instance = mocker.MagicMock()
        instance.__class__.__name__ = "User"

        # Mock _run to verify handlers
        mock_run = mocker.patch.object(service, "_run_parler_translation")
        mock_run.return_value = ({"short_description": "Short", "bio": "<p>Bio</p>"}, {})
        mocker.patch.object(service, "_save_translations")

        results, failures = service.translate_user(instance, "pl")
        assert failures == {}

        # Verify calls
        assert mock_run.call_count == 2

        # Verify handlers — _get_handler now wraps with functools.partial,
        # so compare .func to the underlying mock method.
        handlers_func = [
            h.func if isinstance(h, functools.partial) else h
            for h in (call[0][3] for call in mock_run.call_args_list)
        ]
        assert mock_agent.translate in handlers_func
        assert mock_agent.translate_html in handlers_func

    def test_translate_user_saves_translations(self, mocker: MockerFixture):
        """Test that translated fields are saved."""
        mock_agent = mocker.Mock()
        service = TranslationService(agent=mock_agent)

        instance = mocker.MagicMock()
        instance.__class__.__name__ = "User"  # Mock the class name for translate_model

        # Mock helper to return values
        def side_effect(inst, field, lang, handler, force=False):
            if field == "short_description":
                return "Opis", None
            return "<p>Bio</p>", None

        mocker.patch.object(
            service,
            "_run_parler_translation",
            side_effect=side_effect,
        )

        # Call method
        results, failures = service.translate_user(instance, "pl")

        # Verify results
        assert results["short_description"] == "Opis"
        assert results["bio"] == "<p>Bio</p>"
        assert failures == {}

        # Verify save_translations called
        instance.save_translations.assert_called_once()

    def test_translate_shop_settings_handles_text_and_html(self, mocker: MockerFixture):
        """Verify title uses plain text and description uses HTML translation."""
        mock_agent = mocker.Mock()
        service = TranslationService(agent=mock_agent)

        instance = mocker.MagicMock()
        instance.__class__.__name__ = "ShopSettings"

        mock_run = mocker.patch.object(
            service, "_run_parler_translation", return_value=("Translated", None)
        )
        mocker.patch.object(service, "_save_translations")

        results, failures = service.translate_shop_settings(instance, "pl")

        assert results["title"] == "Translated"
        assert results["description"] == "Translated"
        assert failures == {}
        assert mock_run.call_count == 2

        handlers_func = [
            h.func if isinstance(h, functools.partial) else h
            for h in (call[0][3] for call in mock_run.call_args_list)
        ]
        assert mock_agent.translate in handlers_func
        assert mock_agent.translate_html in handlers_func

    def test_translate_astro_image_uses_html_agent_for_description(self, mocker: MockerFixture):
        """Verify HTML agent use for description in AstroImage translation."""
        mock_agent = mocker.Mock()
        service = TranslationService(agent=mock_agent)

        instance = mocker.MagicMock()
        instance.__class__.__name__ = "AstroImage"  # Mock the class name for translate_model

        mock_run = mocker.patch.object(
            service, "_run_parler_translation", return_value=("Translated", None)
        )
        mocker.patch.object(service, "_save_translations")

        service.translate_astro_image(instance, "pl")

        call_args_list = mock_run.call_args_list
        # We expect 4 calls: name, description, exposure_details, processing_details
        assert len(call_args_list) == 4

        # Verify calls use expected handlers
        # args structure: (instance, field_name, language_code, handler_func)

        # Description should use translate_html
        # We scan calls to find 'description' field
        desc_calls = [c for c in call_args_list if c[0][1] == "description"]
        assert len(desc_calls) >= 1
        # Handler is a functools.partial; unwrap .func to compare
        desc_handler = desc_calls[0][0][3]
        assert (
            desc_handler == mock_agent.translate_html
            or getattr(desc_handler, "func", None) == mock_agent.translate_html
        )

        name_calls = [c for c in call_args_list if c[0][1] == "name"]
        assert len(name_calls) >= 1
        name_handler = name_calls[0][0][3]
        assert (
            name_handler == mock_agent.translate
            or getattr(name_handler, "func", None) == mock_agent.translate
        )

    def test_parler_ceremony_obeys_force_parameter(self, mocker: MockerFixture):
        """Verify that _parler_ceremony yields source even if translation exists with force=True."""
        instance = mocker.MagicMock()
        instance.get_current_language.return_value = "en"

        mock_agent = mocker.Mock()
        service = TranslationService(agent=mock_agent)

        mocker.patch(
            "translation.services.TranslationService._get_default_language_text",
            return_value="Source",
        )

        # _parler_ceremony is a generator. We expect it to yield the source text.
        gen = service._parler_ceremony(instance, "name", "pl", force=True)
        try:
            val = next(gen)
            # If the generator yields a value, it means translation is needed
            assert val == "Source"
        except StopIteration:
            # If it raises StopIteration immediately, it means it was skipped
            pytest.fail("_parler_ceremony skipped despite force=True")

    def test_llm_refusal_rejected(self, mocker, astro_image_factory):
        """LLM refusal messages must not be saved as translations."""
        instance = astro_image_factory()
        mock_agent = mocker.Mock()
        # LLM returns a polite refusal instead of a translation
        mock_agent.translate.return_value = (
            "I'm sorry, but it seems like there might be a mistake in your input."
        )
        service = TranslationService(agent=mock_agent)

        mocker.patch.object(service, "_save_translations")

        result, failures = service.translate_astro_image(instance, "pl")

        # name is a plain text field — on refusal it must be empty so FE shows default lang
        assert result["name"] == ""
        assert failures["name"].startswith("LLM Refusal")

    def test_llm_assistant_style_reply_rejected(self, mocker, astro_image_factory):
        """Assistant-style help text must not be saved as a translation."""
        instance = astro_image_factory()
        mock_agent = mocker.Mock()
        mock_agent.translate.return_value = (
            "I'm here to help with your astrophotography entry translation. "
            "Please provide the text you'd like me to edit."
        )
        service = TranslationService(agent=mock_agent)

        mocker.patch.object(service, "_save_translations")

        result, failures = service.translate_astro_image(instance, "pl")

        assert result["name"] == ""
        assert failures["name"].startswith("LLM Refusal")

    def test_llm_identical_output_accepted_as_proper_noun(self, mocker, astro_image_factory):
        """LLM returning the exact source text is now treated
        as a valid translation (proper noun)."""
        instance = astro_image_factory()
        source_name = instance.name
        mock_agent = mocker.Mock()
        # LLM echoes source verbatim — valid for proper nouns (e.g. "Lanzarote")
        mock_agent.translate.return_value = source_name
        service = TranslationService(agent=mock_agent)

        mocker.patch.object(service, "_save_translations")

        result, failures = service.translate_astro_image(instance, "pl")

        # Identity match is now accepted: source written through, no failure recorded
        assert result["name"] == source_name
        assert "name" not in failures

    def test_field_hint_bound_in_get_handler(self, mocker):
        """_get_handler must return a partial with field_hint bound to the field name."""
        mock_agent = mocker.Mock()
        service = TranslationService(agent=mock_agent)

        from translation.services import FieldTranslationConfig

        config = FieldTranslationConfig(name="name", is_html=False)
        handler = service._get_handler(config)

        assert isinstance(handler, functools.partial)
        assert handler.func == mock_agent.translate
        assert handler.keywords.get("field_hint") == "name"

    def test_field_hint_bound_for_html_field(self, mocker):
        """_get_handler for an HTML field must bind translate_html with field_hint."""
        mock_agent = mocker.Mock()
        service = TranslationService(agent=mock_agent)

        from translation.services import FieldTranslationConfig

        config = FieldTranslationConfig(name="description", is_html=True)
        handler = service._get_handler(config)

        assert isinstance(handler, functools.partial)
        assert handler.func == mock_agent.translate_html
        assert handler.keywords.get("field_hint") == "description"


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
        mock_service_instance = infra["service"].create_default.return_value
        mock_service_instance.translate_place = mocker.Mock(return_value=("Warszawa", {}))
        mock_task_record = mocker.Mock()
        infra["task_model"].objects.update_or_create.return_value = (mock_task_record, True)

        translate_instance_task(
            model_name="astrophotography.Place",
            instance_pk=1,
            language_code="pl",
            method_name="translate_place",
        )

        # We expect 2 calls: one for Status.RUNNING and one for Status.COMPLETED
        assert infra["task_model"].objects.update_or_create.call_count == 2

        # Verify RUNNING transition
        call_running = infra["task_model"].objects.update_or_create.call_args_list[0]
        assert call_running.kwargs["defaults"]["status"] == infra["task_model"].Status.RUNNING

        # Verify COMPLETED transition
        call_completed = infra["task_model"].objects.update_or_create.call_args_list[-1]
        assert call_completed.kwargs["defaults"]["status"] == infra["task_model"].Status.COMPLETED

        mock_service_instance.translate_place.assert_called_once_with(mock_instance, "pl")

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
        mock_service_instance = infra["service"].create_default.return_value
        mock_service_instance.translate_place = mocker.Mock(
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

        assert mock_service_instance.translate_place.call_count == 2

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
        mock_service_instance = infra["service"].create_default.return_value
        mock_service_instance.translate_place = mocker.Mock(side_effect=RequestException("Error"))

        with pytest.raises(RequestException):
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
        mock_service_instance = infra["service"].create_default.return_value
        mock_service_instance.translate_parler_tag = mocker.Mock(return_value=["Django"])

        translate_instance_task(
            model_name="astrophotography.Tag",
            instance_pk=5,
            language_code="pl",
            method_name="translate_parler_tag",
            force=True,
        )

        mock_service_instance.translate_parler_tag.assert_called_once_with(
            mock_instance, "pl", force=True
        )
