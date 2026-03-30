from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("users", "0014_replace_original_image_fields_with_webp_fields"),
    ]

    operations = [
        migrations.AddField(
            model_name="user",
            name="avatar_cropped",
            field=models.ImageField(
                blank=True,
                help_text="Cropped avatar managed by the admin cropper.",
                null=True,
                upload_to="avatars/",
                verbose_name="Avatar cropped",
            ),
        ),
        migrations.AddField(
            model_name="user",
            name="about_me_image_cropped",
            field=models.ImageField(
                blank=True,
                help_text="Cropped portrait managed by the admin cropper.",
                null=True,
                upload_to="about_me_images/",
                verbose_name="About Me Image cropped",
            ),
        ),
        migrations.AddField(
            model_name="user",
            name="about_me_image2_cropped",
            field=models.ImageField(
                blank=True,
                help_text="Cropped portrait managed by the admin cropper.",
                null=True,
                upload_to="about_me_images/",
                verbose_name="About Me Image 2 cropped",
            ),
        ),
    ]
