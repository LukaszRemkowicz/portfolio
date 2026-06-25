from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("astrophotography", "0020_remove_astroimage_original_webp_and_more"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="astroimage",
            name="thumbnail",
        ),
        migrations.RemoveField(
            model_name="mainpagebackgroundimage",
            name="thumbnail",
        ),
    ]
