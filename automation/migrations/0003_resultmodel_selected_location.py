from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("automation", "0002_resultmodel_selected_dates"),
    ]

    operations = [
        migrations.AddField(
            model_name="resultmodel",
            name="selected_location",
            field=models.CharField(blank=True, max_length=255),
        ),
    ]
