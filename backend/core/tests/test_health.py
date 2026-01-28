# backend/core/tests/test_health.py
import pytest
from rest_framework import status

from django.urls import reverse


@pytest.mark.django_db
def test_health_check_endpoint(api_client):
    """Test that the health check endpoint returns 200 OK and 'healthy' status"""
    url = reverse("health")
    response = api_client.get(url)

    assert response.status_code == status.HTTP_200_OK
    assert response.data == {"status": "healthy"}
