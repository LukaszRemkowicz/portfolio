"""End-to-end checks: the real `submit` runs tasks after commit (no `submit` mock)."""

from collections.abc import Callable
from contextlib import AbstractContextManager
from typing import Any

import pytest
from pytest_mock import MockerFixture
from rest_framework.test import APIClient

from django.core import mail
from django.test import override_settings
from django.urls import reverse

from astrophotography.tests.factories import AstroImageFactory
from core.tests.factories import LandingPageSettingsFactory
from inbox.models import ContactMessage

CaptureOnCommit = Callable[..., AbstractContextManager[Any]]


# Override the root autouse fixtures (immediate on_commit, mocked translation submit) so the
# real `submit` + `transaction.on_commit` path is exercised in this module.
@pytest.fixture(autouse=True)
def execute_on_commit() -> None:
    return None


@pytest.fixture(autouse=True)
def global_translation_mock() -> None:
    return None


@pytest.mark.django_db
@override_settings(
    SIMULATE_CONTACT_EMAILS=False,
    EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
)
def test_contact_form_sends_email_via_real_submit(
    api_client: APIClient, django_capture_on_commit_callbacks: CaptureOnCommit
) -> None:
    LandingPageSettingsFactory(contact_form_enabled=True)
    data = {
        "name": "E2E User",
        "email": "e2e@example.com",
        "subject": "E2E subject",
        "message": "E2E message body",
    }

    with django_capture_on_commit_callbacks(execute=True):
        response = api_client.post(reverse("inbox:contact-message-list"), data, format="json")

    assert response.status_code == 201
    assert ContactMessage.objects.filter(email="e2e@example.com").count() == 1
    # Owner notification + sender confirmation.
    assert len(mail.outbox) == 2
    assert "E2E subject" in mail.outbox[0].subject


@pytest.mark.django_db
def test_translation_runs_via_real_submit(
    mocker: MockerFixture, django_capture_on_commit_callbacks: CaptureOnCommit
) -> None:
    provider = mocker.MagicMock()
    provider.ask_question.return_value = "Przetłumaczony tekst"
    # Patch the name in translation.services only; other tasks keep their own provider.
    mocker.patch("translation.services.LLMProviderRegistry").get.return_value = provider

    with django_capture_on_commit_callbacks(execute=True):
        img = AstroImageFactory(name="Deep Sky Object")

    img.refresh_from_db()
    assert provider.ask_question.called
    assert img.safe_translation_getter("name", language_code="pl", any_language=False) == (
        "Przetłumaczony tekst"
    )
