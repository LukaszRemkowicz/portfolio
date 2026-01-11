from django.db import migrations


def move_data_to_profiles(apps, schema_editor):
    User = apps.get_model("users", "User")
    PersonaProfile = apps.get_model("users", "PersonaProfile")

    owner = User.objects.first()
    if not owner:
        return

    # Create Programming Profile
    PersonaProfile.objects.get_or_create(
        user=owner,
        type="PROGRAMMING",
        defaults={
            "title": "Software Engineer",
            "specific_bio": "Programming bio content",
            "github_url": owner.github_profile,
            "linkedin_url": owner.linkedin_profile,
        },
    )

    # Create Astro Profile
    PersonaProfile.objects.get_or_create(
        user=owner,
        type="ASTRO",
        defaults={
            "title": "Astrophotographer",
            "specific_bio": "Astrophotography bio content",
            "astrobin_url": owner.astrobin_url,
            "fb_url": owner.fb_url,
            "ig_url": owner.ig_url,
        },
    )


def reverse_move_data(apps, schema_editor):
    PersonaProfile = apps.get_model("users", "PersonaProfile")
    PersonaProfile.objects.all().delete()


class Migration(migrations.Migration):
    dependencies = [
        ("users", "0006_alter_user_astrobin_url_alter_user_bio_and_more"),
    ]

    operations = [
        migrations.RunPython(move_data_to_profiles, reverse_move_data),
    ]
