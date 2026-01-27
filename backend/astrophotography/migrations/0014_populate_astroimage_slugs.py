from django.db import migrations
from django.utils.text import slugify


def populate_slugs(apps, schema_editor):
    AstroImage = apps.get_model("astrophotography", "AstroImage")
    for image in AstroImage.objects.all():
        if not image.slug:
            base_slug = slugify(image.name)
            slug = base_slug
            n = 1
            # Check for conflict among currently processing items or existing ones.
            # (Though in this migration context, we are the only writer, but collisions might exist in DB if names are duped)
            while AstroImage.objects.filter(slug=slug).exclude(pk=image.pk).exists():
                slug = f"{base_slug}-{n}"
                n += 1
            image.slug = slug
            image.save()


class Migration(migrations.Migration):

    dependencies = [
        ("astrophotography", "0013_astroimage_slug"),
    ]

    operations = [
        migrations.RunPython(populate_slugs),
    ]
