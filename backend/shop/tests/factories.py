# backend/shop/tests/factories.py

import factory
from factory.django import DjangoModelFactory

from astrophotography.tests.factories import AstroImageFactory
from shop.models import ShopProduct


class ShopProductFactory(DjangoModelFactory):
    """Factory for ShopProduct — creates a minimal valid instance."""

    class Meta:
        model = ShopProduct

    image = factory.SubFactory(AstroImageFactory)
    title = factory.Faker("catch_phrase")
    description = factory.Faker("paragraph")

    price = factory.Faker("pydecimal", left_digits=4, right_digits=2, positive=True)
    currency = "USD"
    external_url = factory.Faker("url")
    is_active = True


class InactiveShopProductFactory(ShopProductFactory):
    """Factory for a product that should NOT appear in public listings."""

    is_active = False
