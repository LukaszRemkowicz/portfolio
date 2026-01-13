from typing import Any, Generator

import pytest


@pytest.fixture
def api_client() -> Any:
    """Create a DRF APIClient instance"""
    from rest_framework.test import APIClient

    return APIClient()


@pytest.fixture
def client() -> Any:
    """Django test client fixture"""
    from django.test import Client

    return Client()


@pytest.fixture(autouse=True)
def clear_django_cache() -> Generator[None, None, None]:
    """
    Automatically clear cache for all tests to ensure isolation.
    """
    from django.core.cache import cache as django_cache

    django_cache.clear()
    yield
    django_cache.clear()


@pytest.fixture
def request_factory() -> Any:
    """Create RequestFactory instance for testing"""
    from django.test import RequestFactory

    return RequestFactory()


@pytest.fixture
def api_request_factory() -> Any:
    """DRF API Request Factory fixture"""
    from rest_framework.test import APIRequestFactory

    return APIRequestFactory()
