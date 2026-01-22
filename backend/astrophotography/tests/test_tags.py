import pytest

from astrophotography.serializers import AstroImageSerializerList
from astrophotography.tests.factories import AstroImageFactory


@pytest.mark.django_db
def test_tags_creation_and_retrieval():
    # Create an image
    image = AstroImageFactory()

    # Add tags
    image.tags.add("nebula", "hydrogen")

    # Verify tags are added
    assert image.tags.count() == 2
    assert "nebula" in image.tags.names()

    # Verify serializer output
    serializer = AstroImageSerializerList(image)
    data = serializer.data

    assert "tags" in data
    assert "nebula" in data["tags"]
    assert "hydrogen" in data["tags"]


@pytest.mark.django_db
def test_tags_view_category_filtering(api_client):
    from django.urls import reverse

    # Setup: 2 images in different categories sharing the same tag
    # Image 1: Landscape category, tag 'night'
    img1 = AstroImageFactory(celestial_object="Landscape")
    img1.tags.add("night")

    # Image 2: Deep Sky category, tags 'night' and 'galaxy'
    img2 = AstroImageFactory(celestial_object="Deep Sky")
    img2.tags.add("night", "galaxy")

    url = reverse("astroimages:tags-list")

    # 1. No filter - should see all tags with total counts
    response = api_client.get(url)
    assert response.status_code == 200
    tags_data = {t["slug"]: t["count"] for t in response.data}
    assert tags_data["night"] == 2
    assert tags_data["galaxy"] == 1

    # 2. Filter by Landscape - should only see 'night' tag with count 1
    response = api_client.get(url, {"filter": "Landscape"})
    assert response.status_code == 200
    tags_data = {t["slug"]: t["count"] for t in response.data}
    assert tags_data["night"] == 1
    assert "galaxy" not in tags_data

    # 3. Filter by Deep Sky - should see 'night' and 'galaxy' with count 1
    response = api_client.get(url, {"filter": "Deep Sky"})
    assert response.status_code == 200
    tags_data = {t["slug"]: t["count"] for t in response.data}
    assert tags_data["night"] == 1
    assert tags_data["galaxy"] == 1
