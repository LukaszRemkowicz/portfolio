# backend/core/tests/test_caching.py

from unittest.mock import patch

import pytest
from rest_framework import status

from django.core.cache import cache
from django.urls import reverse

from astrophotography.tests.factories import AstroImageFactory
from users.tests.factories import UserFactory


@pytest.mark.django_db
class TestApiCaching:
    @pytest.fixture(autouse=True)
    def setup(self):
        cache.clear()
        self.profile_url = reverse("users:profile-profile")
        self.images_url = reverse("astroimages:astroimage-list")
        yield
        cache.clear()

    def test_user_profile_is_cached(self, api_client):
        """Test that the user profile response is cached after the first request."""
        UserFactory()

        # First request - Cache MISS
        with patch("django.core.cache.cache.get", wraps=cache.get) as mock_get:
            response1 = api_client.get(self.profile_url)
            assert response1.status_code == status.HTTP_200_OK
            # Dispatch calls get
            assert mock_get.called

        # Second request - Cache HIT
        with patch("common.decorators.cache.logger.debug") as mock_logger:
            response2 = api_client.get(self.profile_url)
            assert response2.status_code == status.HTTP_200_OK
            assert response2.json() == response1.data

            # Verify logger reported a HIT
            args = [call.args[0] for call in mock_logger.call_args_list]
            assert any("Cache HIT" in arg for arg in args)

    def test_cache_invalidation_on_user_update(self, api_client):
        """Test that updating a user invalidates its cache via signals."""
        user = UserFactory(first_name="Original")

        # Cache MISS
        api_client.get(self.profile_url)

        # Update user - should trigger signal
        user.first_name = "Updated"
        user.save()

        # Second request - should be MISS and return updated data
        with patch("common.decorators.cache.logger.debug") as mock_logger:
            response = api_client.get(self.profile_url)
            assert response.data["first_name"] == "Updated"

            # Verify logger reported a MISS
            args = [call.args[0] for call in mock_logger.call_args_list]
            assert any("Cache MISS" in arg for arg in args)

    def test_cache_returns_304_on_etag_match(self, api_client):
        """Test that the API returns 304 if the If-None-Match header matches the cached ETag."""
        UserFactory()

        # 1. Warm up cache and get ETag
        response1 = api_client.get(self.profile_url)
        etag = response1.get("ETag")
        assert etag is not None

        # 2. Request with If-None-Match
        response2 = api_client.get(self.profile_url, HTTP_IF_NONE_MATCH=etag)

        # Should return 304 Not Modified
        assert response2.status_code == status.HTTP_304_NOT_MODIFIED
        assert response2.content == b""

    def test_cache_invalidation_on_astroimage_create(self, api_client):
        """Test that creating a new AstroImage invalidates the image list cache."""
        AstroImageFactory()

        # 1. Warm up cache
        api_client.get(self.images_url)

        # 2. Create new image - should trigger signal
        AstroImageFactory(name="New Image")

        # 3. Request - should be MISS
        with patch("common.decorators.cache.logger.debug") as mock_logger:
            response = api_client.get(self.images_url)
            assert any(img["name"] == "New Image" for img in response.data)

            # Verify MISS
            args = [call.args[0] for call in mock_logger.call_args_list]
            assert any("Cache MISS" in arg for arg in args)

    def test_cache_invalidation_on_tag_update(self, api_client):
        """Test that updating a tag invalidates the relevant caches."""
        from astrophotography.tests.factories import TagFactory

        tag = TagFactory(name="Old Tag")
        # Tag must be associated with an image to show up in stats
        img = AstroImageFactory()
        img.tags.add(tag)

        tags_url = reverse("astroimages:tags-list")

        # 1. Warm up cache
        api_client.get(tags_url)

        # 2. Update tag - should trigger signal
        tag.name = "Updated Tag"
        tag.save()

        # 3. Request - should be MISS
        with patch("common.decorators.cache.logger.debug") as mock_logger:
            response = api_client.get(tags_url)
            assert any(t["name"] == "Updated Tag" for t in response.data)
            assert any("Cache MISS" in call.args[0] for call in mock_logger.call_args_list)

    def test_cache_invalidation_on_mainpagelocation_create(self, api_client):
        """Test that creating a new MainPageLocation invalidates the travel highlights cache."""
        from astrophotography.tests.factories import MainPageLocationFactory

        MainPageLocationFactory()
        travel_url = reverse("astroimages:travel-highlights-list")

        # 1. Warm up cache
        api_client.get(travel_url)

        # 2. Create new location
        MainPageLocationFactory()

        # 3. Request - should be MISS
        with patch("common.decorators.cache.logger.debug") as mock_logger:
            api_client.get(travel_url)
            assert any("Cache MISS" in call.args[0] for call in mock_logger.call_args_list)

    def test_cache_handles_multiple_languages(self, api_client):
        """Test that different LANGUAGE_CODEs result in different cache entries."""
        user = UserFactory()
        # Set English description (should exist from factory, but let's be sure)
        user.set_current_language("en")
        user.short_description = "English Description"
        user.save()

        # Create Polish translation
        user.create_translation("pl", short_description="Polish Description")

        # 1. Request in English
        response_en = api_client.get(self.profile_url, HTTP_ACCEPT_LANGUAGE="en")
        assert response_en.data["short_description"] == "English Description"

        # 2. Request in Polish
        response_pl = api_client.get(self.profile_url, HTTP_ACCEPT_LANGUAGE="pl")
        assert response_pl.data["short_description"] == "Polish Description"

        # 3. Verify they are cached separately (HIT for each)
        with patch("common.decorators.cache.logger.debug") as mock_logger:
            api_client.get(self.profile_url, HTTP_ACCEPT_LANGUAGE="en")
            api_client.get(self.profile_url, HTTP_ACCEPT_LANGUAGE="pl")

            hits = [
                call.args[0] for call in mock_logger.call_args_list if "Cache HIT" in call.args[0]
            ]
            assert len(hits) >= 2

    def test_cache_invalidation_on_translation_update(self, api_client):
        """Test that updating a translation model clears the cache."""
        user = UserFactory()
        user.set_current_language("en")
        user.short_description = "Initial"
        user.save()

        # Warm cache
        api_client.get(self.profile_url, HTTP_ACCEPT_LANGUAGE="en")

        # Update translation model directly - should trigger signal
        translation = user.get_translation("en")
        translation.short_description = "Updated"
        translation.save()

        # Should be a MISS
        with patch("common.decorators.cache.logger.debug") as mock_logger:
            response = api_client.get(self.profile_url, HTTP_ACCEPT_LANGUAGE="en")
            assert response.data["short_description"] == "Updated"
            assert any("Cache MISS" in call.args[0] for call in mock_logger.call_args_list)
