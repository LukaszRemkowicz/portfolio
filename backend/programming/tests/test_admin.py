import pytest
from bs4 import BeautifulSoup

from django.urls import reverse

from programming.tests.factories import ProjectFactory


@pytest.mark.django_db
class TestProjectAdmin:
    def test_changelist_renders(self, admin_client):
        ProjectFactory(name="Listed")
        response = admin_client.get(reverse("admin:programming_project_changelist"))
        assert response.status_code == 200
        assert b"Listed" in response.content

    def test_add_view_has_pricing_fields(self, admin_client):
        response = admin_client.get(reverse("admin:programming_project_add"))
        for name in (b'name="pricing"', b'name="price"', b'name="currency"'):
            assert name in response.content

    def test_add_view_injects_cropper(self, admin_client):
        response = admin_client.get(reverse("admin:programming_project_add"))
        assert response.status_code == 200
        field = response.context["admin_image_cropper"]["fields"][0]
        assert field["crop_aspect_ratio"] == pytest.approx(16 / 10)
        assert (field["output_width"], field["output_height"]) == (1600, 1000)
        assert BeautifulSoup(response.content, "html.parser").select_one(
            "[data-admin-image-cropper-root]"
        )

    def test_change_view_shows_translation_status(self, admin_client):
        project = ProjectFactory()
        response = admin_client.get(reverse("admin:programming_project_change", args=[project.pk]))
        assert response.status_code == 200
        assert b"Translation Status" in response.content
