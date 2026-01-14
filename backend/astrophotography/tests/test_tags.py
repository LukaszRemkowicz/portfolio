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
