from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("programming", "0011_remove_projectimage_original_webp"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="projectimage",
            name="thumbnail",
        ),
    ]
