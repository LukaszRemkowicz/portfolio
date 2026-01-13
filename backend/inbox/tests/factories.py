import factory
from factory.django import DjangoModelFactory

from inbox.models import ContactFormSettings, ContactMessage


class ContactMessageFactory(DjangoModelFactory):
    class Meta:
        model = ContactMessage

    name = factory.Faker("name")
    email = factory.Faker("email")
    subject = factory.Faker("sentence", nb_words=4)
    message = factory.Faker("paragraph", nb_sentences=3)


class ContactFormSettingsFactory(DjangoModelFactory):
    class Meta:
        model = ContactFormSettings
        django_get_or_create = ("pk",)

    pk = 1
    enabled = False
