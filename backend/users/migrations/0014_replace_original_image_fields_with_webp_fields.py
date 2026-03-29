from django.db import migrations, models


def migrate_user_image_fields(apps, schema_editor):
    User = apps.get_model("users", "User")

    field_mappings = [
        ("avatar", "avatar_original_image", "avatar_webp"),
        ("about_me_image", "about_me_image_original_image", "about_me_image_webp"),
        ("about_me_image2", "about_me_image2_original_image", "about_me_image2_webp"),
    ]

    for user in User.objects.all():
        update_kwargs = {}

        for source_field, original_field, webp_field in field_mappings:
            current_name = str(getattr(user, source_field) or "")
            original_name = str(getattr(user, original_field) or "")

            if original_name:
                update_kwargs[source_field] = original_name
                if current_name:
                    update_kwargs[webp_field] = current_name
                continue

            if current_name.lower().endswith(".webp"):
                update_kwargs[webp_field] = current_name

        if update_kwargs:
            User.objects.filter(pk=user.pk).update(**update_kwargs)


class Migration(migrations.Migration):
    dependencies = [
        ("users", "0013_alter_user_about_me_image2_original_image_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="user",
            name="avatar_webp",
            field=models.ImageField(
                blank=True,
                editable=False,
                help_text="Derived WebP avatar generated from the source avatar.",
                null=True,
                upload_to="avatars/",
                verbose_name="Avatar WebP",
            ),
        ),
        migrations.AddField(
            model_name="user",
            name="about_me_image_webp",
            field=models.ImageField(
                blank=True,
                editable=False,
                help_text="Derived WebP portrait generated from the source about_me_image.",
                null=True,
                upload_to="about_me_images/",
                verbose_name="About Me Image WebP",
            ),
        ),
        migrations.AddField(
            model_name="user",
            name="about_me_image2_webp",
            field=models.ImageField(
                blank=True,
                editable=False,
                help_text="Derived WebP portrait generated from the source about_me_image2.",
                null=True,
                upload_to="about_me_images/",
                verbose_name="About Me Image 2 WebP",
            ),
        ),
        migrations.RunPython(migrate_user_image_fields, migrations.RunPython.noop),
        migrations.RemoveField(
            model_name="user",
            name="avatar_original_image",
        ),
        migrations.RemoveField(
            model_name="user",
            name="about_me_image_original_image",
        ),
        migrations.RemoveField(
            model_name="user",
            name="about_me_image2_original_image",
        ),
    ]
