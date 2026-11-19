import factory
from factory.django import DjangoModelFactory

from programming.models import Project


class ProjectFactory(DjangoModelFactory):
    class Meta:
        model = Project

    name = factory.Faker("catch_phrase")
    description = factory.Faker("paragraph")
    technologies = "Python, Django, React"
    github_url = factory.Faker("url")
    live_url = factory.Faker("url")
    image = factory.django.ImageField(width=1600, height=1000)
