"""End-to-end checks: the real `submit` runs tasks after commit (no `submit` mock)."""

from collections.abc import Callable
from contextlib import AbstractContextManager
from typing import Any

import pytest
from pytest_mock import MockerFixture

from astrophotography.tests.factories import AstroImageFactory

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
