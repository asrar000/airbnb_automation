from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="ResultModel",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("test_case", models.CharField(max_length=255)),
                ("url", models.URLField(blank=True, max_length=500)),
                ("passed", models.BooleanField(default=False)),
                ("comment", models.TextField(blank=True)),
                ("screenshot_path", models.CharField(blank=True, max_length=500)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
            ],
            options={"verbose_name": "Result model", "verbose_name_plural": "Result models", "ordering": ["-created_at"]},
        ),
        migrations.CreateModel(
            name="AutoSuggestionItem",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("index", models.PositiveIntegerField()),
                ("text", models.CharField(max_length=500)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("result", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="suggestions", to="automation.resultmodel")),
            ],
            options={"ordering": ["index"]},
        ),
        migrations.CreateModel(
            name="ListingItem",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("title", models.CharField(blank=True, max_length=500)),
                ("price", models.CharField(blank=True, max_length=100)),
                ("image_url", models.URLField(blank=True, max_length=1000)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("result", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="listings", to="automation.resultmodel")),
            ],
        ),
        migrations.CreateModel(
            name="ListingDetail",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("title", models.CharField(blank=True, max_length=500)),
                ("subtitle", models.CharField(blank=True, max_length=500)),
                ("image_urls", models.TextField(blank=True, help_text="Newline-separated image URLs")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("result", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="details", to="automation.resultmodel")),
            ],
        ),
        migrations.CreateModel(
            name="NetworkLog",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("method", models.CharField(blank=True, max_length=10)),
                ("url", models.URLField(blank=True, max_length=2000)),
                ("status", models.IntegerField(blank=True, null=True)),
                ("resource_type", models.CharField(blank=True, max_length=50)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("result", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="network_logs", to="automation.resultmodel")),
            ],
        ),
        migrations.CreateModel(
            name="ConsoleLog",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("log_type", models.CharField(choices=[("log", "Log"), ("warn", "Warning"), ("error", "Error"), ("info", "Info")], default="log", max_length=10)),
                ("message", models.TextField(blank=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("result", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="console_logs", to="automation.resultmodel")),
            ],
        ),
    ]
