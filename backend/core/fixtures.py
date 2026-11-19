from collections.abc import Generator

import pytest

from django.core.cache import cache as django_cache
from django.test import Client, RequestFactory


@pytest.fixture
def client() -> Client:
    """Django test client fixture"""
    return Client()


@pytest.fixture(autouse=True)
def clear_django_cache() -> Generator[None]:
    """
    Automatically clear cache for all tests to ensure isolation.
    """
    django_cache.clear()
    yield
    django_cache.clear()


@pytest.fixture
def request_factory() -> RequestFactory:
    """Create RequestFactory instance for testing"""
    return RequestFactory()
