from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("automation", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="resultmodel",
            name="selected_month",
            field=models.CharField(blank=True, max_length=100),
        ),
        migrations.AddField(
            model_name="resultmodel",
            name="checkin_date",
            field=models.CharField(blank=True, max_length=100),
        ),
        migrations.AddField(
            model_name="resultmodel",
            name="checkout_date",
            field=models.CharField(blank=True, max_length=100),
        ),
    ]
