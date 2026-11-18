from unittest.mock import patch

import pytest

from django.urls import reverse

from common.tests.image_helpers import jpeg_field
from programming.models import ProjectImage
from programming.tests.factories import ProjectFactory


@pytest.mark.django_db
def test_standalone_project_image_admin_save(admin_client):
    project = ProjectFactory()
    with patch("core.models.submit"):
        response = admin_client.post(
            reverse("admin:programming_projectimage_add"),
            {
                "project": project.pk,
                "name": "Admin image",
                "description": "Example",
                "original_upload": jpeg_field("upload.jpg"),
                "_save": "Save",
            },
        )
    assert response.status_code == 302
    assert ProjectImage.objects.filter(project=project).count() == 1
