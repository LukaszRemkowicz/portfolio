import factory
from factory.django import DjangoModelFactory

from programming.models import ProgrammingPageConfig, Project, ProjectImage


class ProjectFactory(DjangoModelFactory):
    class Meta:
        model = Project

    name = factory.Faker("catch_phrase")
    description = factory.Faker("paragraph")
    technologies = "Python, Django, React"
    github_url = factory.Faker("url")
    live_url = factory.Faker("url")


class ProjectImageFactory(DjangoModelFactory):
    class Meta:
        model = ProjectImage

    project = factory.SubFactory(ProjectFactory)
    image = factory.django.ImageField()
    is_cover = False


class ProgrammingPageConfigFactory(DjangoModelFactory):
    class Meta:
        model = ProgrammingPageConfig
        django_get_or_create = ("pk",)

    pk = 1
    enabled = False
