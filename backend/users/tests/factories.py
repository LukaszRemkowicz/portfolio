import factory
from factory.django import DjangoModelFactory

from users.models import Profile, User


class UserFactory(DjangoModelFactory):
    class Meta:
        model = User
        django_get_or_create = ("email",)

    email = "admin@example.com"
    first_name = "Admin"
    last_name = "User"
    bio = "General bio"
    is_active = True
    is_staff = True
    is_superuser = True


class ProfileFactory(DjangoModelFactory):
    class Meta:
        model = Profile

    user = factory.SubFactory(UserFactory)
    is_active = True
    title = factory.Faker("job")
    specific_bio = factory.Faker("paragraph")


class ProgrammingProfileFactory(ProfileFactory):
    type = Profile.ProfileType.PROGRAMMING
    title = "Dev"
    specific_bio = "Bio"
    github_url = ""
    linkedin_url = ""


class AstroProfileFactory(ProfileFactory):
    type = Profile.ProfileType.ASTRO
    title = "Astro"
    specific_bio = "Bio"
    astrobin_url = ""
    fb_url = ""
    ig_url = ""
