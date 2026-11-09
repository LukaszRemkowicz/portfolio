from django.db import migrations


def rename_astroimage_variant_role(apps, schema_editor, *, old_role, new_role):
    image_variant_model = apps.get_model("core", "ImageVariant")
    database_alias = schema_editor.connection.alias
    image_variant_model.objects.using(database_alias).filter(
        content_type__app_label="astrophotography",
        content_type__model="astroimage",
        role=old_role,
    ).update(role=new_role)


def forwards(apps, schema_editor):
    rename_astroimage_variant_role(
        apps,
        schema_editor,
        old_role="original_format",
        new_role="high_resolution",
    )


def backwards(apps, schema_editor):
    rename_astroimage_variant_role(
        apps,
        schema_editor,
        old_role="high_resolution",
        new_role="original_format",
    )


class Migration(migrations.Migration):
    dependencies = [
        ("astrophotography", "0022_mainpagelocation_legacy_slugs"),
        ("core", "0008_remove_landingpagesettings_serve_webp_images_and_more"),
    ]

    operations = [migrations.RunPython(forwards, backwards)]
