from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("users", "0011_alter_user_about_me_image2_legacy_and_more"),
    ]

    operations = [
        migrations.RenameField(
            model_name="user",
            old_name="avatar_legacy",
            new_name="avatar_original_image",
        ),
        migrations.RenameField(
            model_name="user",
            old_name="about_me_image_legacy",
            new_name="about_me_image_original_image",
        ),
        migrations.RenameField(
            model_name="user",
            old_name="about_me_image2_legacy",
            new_name="about_me_image2_original_image",
        ),
        migrations.AlterField(
            model_name="user",
            name="avatar_original_image",
            field=models.ImageField(
                blank=True,
                editable=False,
                help_text="Original avatar before WebP conversion. Used for rollback.",
                null=True,
                upload_to="avatars/",
                verbose_name="Original Avatar",
            ),
        ),
        migrations.AlterField(
            model_name="user",
            name="about_me_image_original_image",
            field=models.ImageField(
                blank=True,
                editable=False,
                help_text="Original about_me_image before WebP conversion. Used for rollback. TODO: Will be removed in future versions.",
                null=True,
                upload_to="about_me_images/",
                verbose_name="Original About Me Image",
            ),
        ),
        migrations.AlterField(
            model_name="user",
            name="about_me_image2_original_image",
            field=models.ImageField(
                blank=True,
                editable=False,
                help_text="Original about_me_image2 before WebP conversion. Used for rollback. TODO: Will be removed in future versions.",
                null=True,
                upload_to="about_me_images/",
                verbose_name="Original About Me Image 2",
            ),
        ),
    ]
