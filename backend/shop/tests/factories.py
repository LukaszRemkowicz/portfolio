# backend/shop/tests/factories.py

import factory
from factory.django import DjangoModelFactory

from shop.models import ShopProduct


class ShopProductFactory(DjangoModelFactory):
    """Factory for ShopProduct — creates a minimal valid instance."""

    class Meta:
        model = ShopProduct

    # BaseImage requires `path`; use factory's ImageField to generate a real file
    path = factory.django.ImageField(filename="product.jpg", color="blue", format="JPEG")

    # Translated fields: factory-boy sets these on the default language (EN)
    title = factory.Faker("catch_phrase")
    description = factory.Faker("paragraph")

    price = factory.Faker("pydecimal", left_digits=4, right_digits=2, positive=True)
    currency = "USD"
    external_url = factory.Faker("url")
    is_active = True
    order = factory.Sequence(lambda n: n)


class InactiveShopProductFactory(ShopProductFactory):
    """Factory for a product that should NOT appear in public listings."""

    is_active = False
